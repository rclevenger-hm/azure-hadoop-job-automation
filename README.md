# Azure Hadoop Job Automation

An asynchronous, authenticated control plane for **Hadoop JAR / MapReduce jobs on existing Azure HDInsight clusters**. It preserves the OCI request fields and adds durable status, cancellation, history, quotas, idempotency and bounded launcher logs.

## What is included

- Python 3.12 Azure Functions: a private Entra-authenticated HTTP API and a separate queue/timer worker.
- Cosmos DB transactions couple each admission to its daily quota counter. Conditional writes prevent duplicate dispatch and preserve cancellation races.
- Native WebHCat `mapreduce/jar` submission. A lost response triggers identity-checked reconciliation, never a blind resubmission.
- Private Storage Queue with poison handling, managed identities, private endpoints, TLS, continuous database backup, alerts and a resource-group budget.
- Hash-locked dependencies, deterministic source packaging, 144 automated tests, Terraform mock plans and manual OIDC deployment.

The Terraform provisions the control plane. You supply an existing Hadoop-capable HDInsight cluster, its storage and networking, and an Entra API registration. No cloud resources are deployed by CI.

## Quick start

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.txt
python -m pytest
ruff check app tests scripts function_app.py
python scripts/check_contract.py
python scripts/build.py
```

Follow [deployment](docs/DEPLOYMENT.md) for Azure prerequisites, private runner access, Terraform and package publishing. The [API guide](docs/API.md) and [OpenAPI contract](openapi.yaml) describe requests and responses.

## Submit a job

Use a version 2 Microsoft Entra access token with the API application's client ID as its audience. Each caller's immutable object ID must be authorized by the selected profile.

```bash
python scripts/client.py --url https://YOUR-APP.azurewebsites.net \
  --scope api://YOUR-API-CLIENT-ID/.default submit examples/job.json \
  --key unique-request-001
```

```json
{
  "profile": "analytics",
  "jar_path": "abfss://jobs@yourstorage.dfs.core.windows.net/jars/wordcount.jar",
  "job_class": "com.example.WordCount",
  "input_path": "abfss://jobs@yourstorage.dfs.core.windows.net/input/words.txt",
  "output_path": "abfss://jobs@yourstorage.dfs.core.windows.net/output/unique-run-001",
  "arguments": []
}
```

The API returns `202` and a stable job ID. Replaying the same key and inputs returns `200` without charging quota again. Query `GET /jobs/{job_id}`, `GET /jobs`, `GET /usage`, or `GET /jobs/{job_id}/logs`; cancel with `POST /jobs/{job_id}/cancel`.

## Execution guarantees

The worker commits `SUBMITTING` before one non-retrying HTTPS submission. It records a random, durable status directory and verifies the remote job's owner, JAR, class, complete argument vector and status directory during recovery and polling. A crash before the POST can therefore leave an unstarted job in review: avoiding duplicate execution takes priority over automatic progress when the outcome cannot be proven.

`NEEDS_REVIEW` requires an operator decision. It never proves that a remote job stopped. Cancellation acknowledgment is not terminal cancellation, and a successful WebHCat launcher is not success until its child process exit value is available. Applications must design their own idempotent output writes.

## Documentation

- [Architecture and invariants](docs/ARCHITECTURE.md)
- [Parity with OCI, AWS and GCP](docs/PARITY.md)
- [Security boundaries](docs/SECURITY.md)
- [Operations and recovery](docs/OPERATIONS.md)
- [Validation and limits](docs/VALIDATION.md)
- [Cost controls](docs/COSTS.md)

Commit-date provenance is documented in [NOTICE](NOTICE). Licensed under [MIT](LICENSE).
