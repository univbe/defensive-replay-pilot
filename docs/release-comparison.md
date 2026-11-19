# Compare a release candidate

Use this mode when the same controlled drill was run through two versions of a service. The positional CSV is the **candidate**. The CSV following `--baseline` is the **reference**.

1. Choose the expected drill session and decoy labels before reviewing either result.
2. Collect both exports over matching capture windows. Use consistent opaque session IDs and route labels in both exports. Include ordinary control activity.
3. Run the comparison from the project root.

```sh
python checkout_pilot.py candidate.csv --baseline baseline.csv --drill-session test-drill --decoy fixture-a --decoy fixture-b
```

| Verdict | Exit | Interpretation |
| --- | ---: | --- |
| `PASS` | 0 | Both exports satisfy the rule's pass criteria. Event counts can differ. |
| `REGRESSION` | 1 | Baseline passed and the candidate needs review. Read the candidate's `review_reasons`. |
| `BASELINE_NEEDS_REVIEW` | 1 | The reference failed its own criteria. Check its evidence before attributing a difference to the release. |
| Input error | 2 | A file or option was invalid. No comparison JSON is emitted. |

Both reports are produced by the same local detector. This comparison evaluates **captured behavior**. It does not run the two service builds, verify their provenance, or match individual events across traces. Archive the build references with the reports inside your team's environment if you need that audit trail.

For missing sessions, mismatched route labels and capture-window checks, see the [staging guide](staging.md).
