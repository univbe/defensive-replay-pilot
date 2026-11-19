# Run the detection pilot in staging

Use Python 3.11 or newer. The script runs locally with the standard library. It reads an exported trace and prints JSON to standard output. It makes no network requests and sends no alerts.

1. Choose two distinct decoy route labels in your staging service. Using one dedicated test session, visit both decoys within 60 seconds. Include at least one other session performing ordinary activity in the same export. Keep the expected drill session ID so you can check that the alert identifies the correct session.
2. Export a bounded window of events as UTF-8 CSV with exactly the headers below, in any order. Use ISO 8601 timestamps with a timezone, opaque test-session IDs, and route labels. The script sorts events by time. Labels and IDs match exactly. Omit raw URLs, request bodies, authentication tokens, and customer identifiers.
3. Run the command below on the machine holding the export. Replace the example labels and session ID with your own. Share only the resulting JSON if your team approves disclosure of aggregate traffic counts.

Example input (synthetic):

```csv
event_time,session_id,route_label
2026-01-01T12:00:00Z,test-normal,checkout
2026-01-01T12:00:01Z,test-drill,fixture-a
2026-01-01T12:00:25Z,test-drill,fixture-b
```

```text
python checkout_pilot.py staging.csv --drill-session test-drill --decoy fixture-a --decoy fixture-b
```

**PASS** (exit 0) means the rule alerted on the expected drill session, observed at least one other session, and alerted on none of the others. Two different decoys at exactly 60 seconds count. Repeated visits to one decoy do not qualify. Each session can alert once.

**REVIEW** (exit 1) means a condition above was unmet. Inspect the export locally for missing drill activity, missing control sessions, or unexpected alerts. Invalid input produces a diagnostic on standard error and exits 2 without a report.

The JSON contains the rule version, input type, result, event count, other-session count, drill-detection flag and other-session alert count. It omits filenames, timestamps, identifiers and route labels. The operator supplies the data and can attest where it came from. A pass describes this trace only.

Running `python checkout_pilot.py` without arguments runs the original synthetic self-test.

## Simulated VPN check

Run `python vpn_replay.py` to compare a read-only agent with a deliberately faulty simulated agent. The four-case self-test expects one policy failure when the faulty agent disconnects and reconnects the mock tunnel. All cases run offline.
