# Validation

## Automated checks

Python tests exercise real JWT signature verification, Azure Functions binding indexing, request contracts, concurrent admissions, transactional rollback, compare-and-swap, cancellation races, recovery paging, full remote provenance and bounded logs. The in-memory Cosmos model simulates atomicity and ETags; SDK contract tests additionally verify actual batch serialization. HDInsight transport tests inspect real Requests form encoding and do not submit cluster jobs.

Terraform CI runs formatting, provider initialization with the checked-in lock file, validation and 18 mock plans. These inspect private networking, identity access, protected state, queue poison handling, retention, quotas, alerts and invalid settings. A build check imports each role from the staged production artifact.

## Live acceptance required

From a private Azure runner: deploy to a disposable environment; verify Entra token rejection/acceptance, API ownership, duplicate key response, quota limits, one word-count job, output integrity, stdout/stderr/exit retrieval, cancellation, worker restarts, a simulated lost gateway response, timer recovery and operator alerts. Confirm HTTP error envelopes and userargs fields match the deployed HDInsight WebHCat version. Verify application permissions and network access with a denied principal too.

