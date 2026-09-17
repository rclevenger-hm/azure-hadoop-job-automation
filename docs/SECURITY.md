# Security model

## Caller authentication

The application independently verifies RS256 signatures using a tenant-specific Microsoft JWKS endpoint. It requires issuer, audience, expiry, not-before, issued-at, subject, tenant, object ID and v2 token version. Allowed object IDs are additionally constrained per cluster profile. Incoming identity headers are not trusted. The Function HTTP trigger uses anonymous platform auth because bearer verification is implemented by the application; the endpoint is private and cannot accept unauthenticated application calls.

