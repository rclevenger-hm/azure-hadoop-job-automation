# Operations

## Before enabling dispatch

Confirm cluster type supports WebHCat MapReduce, status storage is writable by the cluster and readable by the API identity, profile prefixes exist, credentials work and private DNS resolves from both Functions and the deployment runner. Run one disposable canary and inspect native job identity, output and logs.

## Unknown outcomes

Inspect the durable job's submission ID, exact statusdir, cluster and submitted time. Search WebHCat job records and compare owner, jar, class and full arg list. Never reset SUBMITTING to QUEUED or replay the POST just because a request timed out. A crash before submission and a lost successful response are indistinguishable until external evidence resolves them. NEEDS_REVIEW does not cancel any remote work.

WebHCat job retention must exceed the 24-hour recovery window, plus operational lag. Reconciliation scans pages in ascending job ID order, so large shared histories can delay recovery. More than one matching job or non-progressing pages stops automatic attachment. Missing/temporarily unavailable already-attached jobs retain their active state and produce reconciliation error telemetry; investigate rather than treating them as failed.

## Queue and cancellation

The jobs-poison queue is retained for investigation. Malformed messages need repair/removal; legitimate jobs can be redispatched by the timer only while QUEUED. The hourly queue count alarm covers total queued/poison backlog; it is not an immediate per-poison-message alarm. Inspect both queues during incidents.

Cancellation is best effort. The request is durable, but Hadoop output can already have been written. Wait for native terminal state. If a poll races cancellation, the ETag protects the newer request. Cancellation that races terminal completion may be observed as SUCCEEDED or FAILED.

## Retention and recovery

Terminal job records expire after configured retention; active records do not expire. Daily counters last three days and rate counters two minutes. Operator-managed statusdir log storage must have a lifecycle policy consistent with job retention. Store outputs independently. On database restoration, stop the worker app, reconcile outstanding native jobs, verify admission counters, then resume deliberately.

## Alerts and diagnosis

Application Insights receives structured api_request, api_error, job_state and reconcile_complete events. Alerts flag API dependency errors, unresolved jobs and reconciliation failures. Check Function execution errors for timer/queue exceptions, queue counts and Cosmos throttling. Resource-group budget emails are advisory and do not cap HDInsight costs.

## Rollback

Redeploy an earlier package only if it understands current state fields. Do not destroy the database or clear queues for rollback. Deployment is manual from a protected main branch and uses a fixed source commit. Record the package digest in the deployment log.
