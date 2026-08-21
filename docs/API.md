# API guide

## Authentication and ownership

Send `Authorization: Bearer TOKEN` with an Entra v2 access token for the configured API client ID. Every request consumes the caller’s per-minute allowance. Profile permissions use the caller’s Entra object ID; job ownership binds both directory and object ID. Use the private Function origin without an `/api` prefix.

