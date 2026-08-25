# Architecture

## Data flow

The private HTTP Function verifies a signed Entra v2 token, applies a caller request limit, validates the selected profile, and atomically creates a Cosmos job plus its daily quota counter. Storage Queue carries only hashed tenant and job IDs. A separate worker loads the server-owned request snapshot, claims it with an ETag and submits to HDInsight. The timer recovers lost queue sends and polls outstanding jobs.

## Partition and identity

The Cosmos partition is SHA-256 of Entra tenant ID plus caller object ID. The job ID hashes that partition and the idempotency key. Jobs and quota counters share the partition so the two writes commit or roll back together. Runtime callers never access Cosmos directly. API ownership always comes from verified claims, not request fields.

A random submission ID and status directory are persisted at admission. Remote job IDs are validated before URL construction. Remote status and cancellation recheck the complete stored input identity. Active jobs have TTL -1; only terminal records expire. An expired key must not be reused; after physical TTL deletion no historical deduplication guarantee remains.

