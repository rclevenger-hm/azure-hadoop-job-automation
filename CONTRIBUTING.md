# Contributing

## Local checks

Install requirements-dev.txt with --require-hashes, run pytest, ruff, scripts/check_contract.py and scripts/build.py. Run Terraform fmt, init -backend=false, validate and test. Do not use real credentials in tests.

## Change invariants

Preserve one-POST dispatch, atomic quota admission, caller ownership, conditional writes and cancellation intent. Add regression coverage for changes to state transitions or SDK contracts. Never replace an unknown outcome with an automatic resubmission. Keep operational limits and OpenAPI in sync.

## Dependencies

Update requirements.in, then regenerate requirements.txt and requirements-dev.txt using pip-compile --generate-hashes --allow-unsafe --strip-extras. Review the audit and production artifact import. Terraform providers remain constrained and locked; update deliberately.
