# Operations

## Before enabling dispatch

Confirm cluster type supports WebHCat MapReduce, status storage is writable by the cluster and readable by the API identity, profile prefixes exist, credentials work and private DNS resolves from both Functions and the deployment runner. Run one disposable canary and inspect native job identity, output and logs.

## Unknown outcomes

Inspect the durable job's submission ID, exact statusdir, cluster and submitted time. Search WebHCat job records and compare owner, jar, class and full arg list. Never reset SUBMITTING to QUEUED or replay the POST just because a request timed out. A crash before submission and a lost successful response are indistinguishable until external evidence resolves them. NEEDS_REVIEW does not cancel any remote work.

WebHCat job retention must exceed the 24-hour recovery window, plus operational lag. Reconciliation scans pages in ascending job ID order, so large shared histories can delay recovery. More than one matching job or non-progressing pages stops automatic attachment. Missing/temporarily unavailable already-attached jobs retain their active state and produce reconciliation error telemetry; investigate rather than treating them as failed.

