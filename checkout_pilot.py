"""Local detection pilot. Run without arguments for the synthetic self-test."""
import argparse
import csv
import json
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from time import perf_counter


def detect(events, decoys):
    """Page once per session for two distinct decoy paths within 60 seconds.

    Events must be ordered by time. Return only the synthetic session and timing.
    """
    recent = defaultdict(deque)
    paged = set()
    alerts = []
    for second, session, path in events:
        if path not in decoys or session in paged:
            continue
        history = recent[session]
        while history and second - history[0][0] > 60:
            history.popleft()
        if any(previous != path for _, previous in history):
            alerts.append((session, second, second - history[0][0]))
            paged.add(session)
        else:
            history.append((second, path))
    return alerts


def replay():
    decoys = {"fixture-a", "fixture-b"}
    normal = [(start + offset, f"shopper-{start}", path)
              for start in range(0, 3600, 6)
              for offset, path in enumerate(("catalog", "cart", "checkout", "receipt"))]
    normal.extend([(100, "monitor", "fixture-a"), (105, "monitor", "fixture-a"),
                   (300, "qa", "fixture-a"), (361, "qa", "fixture-b"),
                   (400, "checker-a", "fixture-a"), (401, "checker-b", "fixture-b")])
    drill = normal + [(900, "drill", "fixture-a"), (924, "drill", "fixture-b"),
                      (926, "drill", "fixture-a")]
    for name, events, expected in [("checkout", normal, []),
                                   ("drill", drill, [("drill", 924, 24)])]:
        ordered = sorted(events)
        started = perf_counter()
        alerts = detect(ordered, decoys)
        elapsed = perf_counter() - started
        if alerts != expected:
            raise AssertionError((name, alerts, expected))
        print(f"{name}: {len(events)} events, alerts={alerts}, replay={elapsed*1000:.3f} ms")


def load_events(filename):
    fields = {"event_time", "session_id", "route_label"}
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    events = []
    with open(filename, newline="", encoding="utf-8-sig") as source:
        rows = csv.DictReader(source, strict=True)
        if len(rows.fieldnames or []) != 3 or set(rows.fieldnames) != fields:
            raise ValueError("Expected exactly event_time, session_id, route_label.")
        for row in rows:
            if None in row or any(not (row[key] or "").strip() for key in fields):
                raise ValueError(f"Missing or extra field at CSV line {rows.line_num}.")
            try:
                stamp = datetime.fromisoformat(row["event_time"].strip().replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    raise ValueError
                seconds = (stamp - epoch).total_seconds()
            except (ValueError, OverflowError):
                raise ValueError(f"Expected a timestamp with timezone at CSV line {rows.line_num}.") from None
            events.append((seconds, row["session_id"], row["route_label"]))
    return sorted(events)


def _drill_evidence(events, decoys, drill_session):
    """Classify the ordered input independently of the detector's output."""
    seen = False
    previous = None
    distinct = set()
    for second, session, label in events:
        if session != drill_session:
            continue
        seen = True
        if label not in decoys:
            continue
        distinct.add(label)
        # The nearest differently labeled pair occurs at a label transition.
        if previous and label != previous[1] and second - previous[0] <= 60:
            return "qualifying_pair"
        previous = (second, label)
    if not seen:
        return "session_absent"
    if not distinct:
        return "no_decoy_visits"
    if len(distinct) == 1:
        return "single_decoy"
    return "outside_window"


def staging_summary(events, decoys, drill_session):
    alerts = detect(events, decoys)
    alerted = {session for session, _, _ in alerts}
    controls = {session for _, session, _ in events if session != drill_session}
    drill_detected = drill_session in alerted
    other_alerts = len(alerted - {drill_session})
    evidence = _drill_evidence(events, decoys, drill_session)
    reasons = []
    if evidence != "qualifying_pair":
        reasons.append(evidence)
    if drill_detected != (evidence == "qualifying_pair"):
        reasons.append("detector_mismatch")
    if not controls:
        reasons.append("no_control_sessions")
    if other_alerts:
        reasons.append("unexpected_alerts")
    return {
        "pilot": "two-distinct-decoys-60s/v1",
        "source": "operator-supplied CSV",
        "result": "REVIEW" if reasons else "PASS",
        "drill_evidence": evidence,
        "review_reasons": reasons,
        "event_count": len(events),
        "other_sessions_seen": len(controls),
        "drill_detected": drill_detected,
        "other_sessions_alerted": other_alerts,
    }


def main():
    if len(sys.argv) == 1:
        replay()
        return 0
    parser = argparse.ArgumentParser(description="Replay a local three-field CSV. Prints aggregate JSON only.")
    parser.add_argument("csv_file")
    parser.add_argument("--decoy", action="append", required=True, help="Decoy route label; repeat for each label.")
    parser.add_argument("--drill-session", required=True, help="Opaque ID of the expected positive session.")
    args = parser.parse_args()
    decoys = set(args.decoy)
    if len(decoys) < 2 or not all(label.strip() for label in decoys) or not args.drill_session.strip():
        parser.error("Specify at least two distinct nonempty decoy labels and a nonempty drill session.")
    try:
        events = load_events(args.csv_file)
    except (UnicodeError, csv.Error, OSError):
        print("Could not read input as UTF-8 CSV.", file=sys.stderr)
        return 2
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    summary = staging_summary(events, decoys, args.drill_session)
    print(json.dumps(summary, indent=2))
    return 0 if summary["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
