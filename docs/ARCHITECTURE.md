# Architecture

## Data flow

The private HTTP Function verifies a signed Entra v2 token, applies a caller request limit, validates the selected profile, and atomically creates a Cosmos job plus its daily quota counter. Storage Queue carries only hashed tenant and job IDs. A separate worker loads the server-owned request snapshot, claims it with an ETag and submits to HDInsight. The timer recovers lost queue sends and polls outstanding jobs.

