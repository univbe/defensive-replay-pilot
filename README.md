# Defensive Replay Pilot

[![Replay checks](https://github.com/univbe/defensive-replay-pilot/actions/workflows/checks.yml/badge.svg)](https://github.com/univbe/defensive-replay-pilot/actions/workflows/checks.yml)

Verify that a checkout detection rule still identifies the intended session after a logging change. Run a known drill through two builds, export three fields from each, and compare the results offline. The tool reports whether the candidate lost a detection or alerted on another session.

[Staging operator guide](docs/staging.md) · [Release comparison](docs/release-comparison.md) · [Example traces](examples/) · [Contributing](CONTRIBUTING.md)

## Quick start

Requires **Python 3.11 or later**. Run from the repository root. The tools use the standard library and require no credentials.

```sh
python checkout_pilot.py examples/checkout-pass.csv --drill-session drill --decoy fixture-a --decoy fixture-b
```

Expected result: `PASS`. The input contains three events across two sessions. Only the drill session visits both decoys within the inclusive 60-second window. Input rows may arrive out of order.

## Find a release regression

```sh
python checkout_pilot.py examples/checkout-incomplete.csv --baseline examples/checkout-pass.csv --drill-session drill --decoy fixture-a --decoy fixture-b
```

This example intentionally exits **1**. The baseline raises the expected alert. The candidate export has only one decoy visit, so the report returns `REGRESSION` with the candidate reason `single_decoy`. That result identifies which logging path to investigate. The export alone cannot establish why the second event is missing.

| Use case | Entry point | Output |
| --- | --- | --- |
| Validate one staging export | `checkout_pilot.py TRACE.csv` with drill and decoy options | Aggregate JSON with evidence and review reasons |
| Compare two release exports | Same command, plus `--baseline BASE.csv` | A verdict and both aggregate reports |
| Exercise a simulated VPN policy | `vpn_replay.py --json` | Four cases showing authorized behavior and an intentionally faulty agent |

## Data handling

The checkout runner reads a bounded CSV into memory. Its report includes counts and fixed diagnostic labels. Filenames, timestamps, session identifiers and route labels stay out of the JSON. Teams can review the aggregate counts before sharing them. The VPN replay uses a scripted agent and an in-memory controller.

## Verification

```sh
python -m unittest discover -s tests -v
python checkout_pilot.py
python vpn_replay.py --json
```

The regression suite runs on Windows and Linux with Python 3.11 and 3.14. Included traces are synthetic. Production performance, adoption and alert quality require separate validation by the service owner.
