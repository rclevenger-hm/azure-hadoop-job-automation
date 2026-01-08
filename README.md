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

