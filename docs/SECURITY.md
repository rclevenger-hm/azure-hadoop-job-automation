# Security model

## Caller authentication

The application independently verifies RS256 signatures using a tenant-specific Microsoft JWKS endpoint. It requires issuer, audience, expiry, not-before, issued-at, subject, tenant, object ID and v2 token version. Allowed object IDs are additionally constrained per cluster profile. Incoming identity headers are not trusted. The Function HTTP trigger uses anonymous platform auth because bearer verification is implemented by the application; the endpoint is private and cannot accept unauthenticated application calls.

## Permissions

API identity: Cosmos data contributor on the one container; job-queue message sender; Blob Data Reader on explicitly supplied log containers; host storage permissions. Worker identity: same Cosmos scope; queue contributor for dispatch, retry and poison handling; Key Vault Secrets User at explicit existing secret ARM scopes; own host storage. API has no cluster credential permission. Both use managed identities, with no account keys or client secrets in Terraform state.

HDInsight's supported basic-auth gateway requires a cluster credential. Store only its password in a version-pinned Key Vault secret and configure the username separately. Vault must use Azure RBAC. Rotation publishes a new version and updates profiles; queued jobs keep their original snapshot, so retain the old credential or drain jobs during cluster-password rotation. This version targets non-ESP/basic-auth clusters, not Entra-enabled/ESP/SPNEGO variants.

## Trusted code and paths

Allowlisted URI prefixes restrict selection, not what arbitrary Hadoop code can do. Only trusted operators may upload JARs to approved prefixes. Do not use this shared cluster account as a hostile multi-tenant sandbox. Optional program arguments are an encoded repeated form field, never an interpolated local shell command. URI traversal, percent encoding, control characters and unknown request fields are rejected.

## Secret and error handling

Passwords, bearer tokens, payloads, remote response bodies and raw exceptions are not logged. Responses use generic dependency errors and request IDs. Status directories use unguessable submission IDs and log requests select one fixed filename, with a 64 KiB maximum. Redirects are disabled on the authenticated HDInsight connection. TLS certificate validation is never disabled.

## State protection

Continuous Cosmos backup and deletion guards protect control state. Recovery of a stale database backup can lose evidence of remote submissions; pause dispatch and reconcile against HDInsight before resuming. An idempotency key only works within the retained record's lifetime. Do not delete active job records as a retry mechanism.
