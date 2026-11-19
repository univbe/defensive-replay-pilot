# Contributing

Use Python 3.11 or later. Run the documented commands from the repository root.

- Add a table-driven case for changes to time windows, session isolation or evidence classification.
- Exercise CLI changes through a subprocess. Check the exit code, stdout and stderr. Use synthetic identifiers when testing privacy.
- Keep the sample CSV files small enough to inspect by eye. Each one should illustrate a specific result.
- Update the operator guide if a new review reason changes what an engineer should check.

Before opening a pull request, run:

```sh
python -m unittest discover -s tests -v
python checkout_pilot.py
python vpn_replay.py --json
```

Describe the input that exposed the issue and the expected verdict. Use synthetic reproductions in public issues and pull requests. Keep staging logs and customer identifiers in the operator's own environment.
