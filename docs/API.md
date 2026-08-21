# API guide

## Authentication and ownership

Send `Authorization: Bearer TOKEN` with an Entra v2 access token for the configured API client ID. Every request consumes the caller’s per-minute allowance. Profile permissions use the caller’s Entra object ID; job ownership binds both directory and object ID. Use the private Function origin without an `/api` prefix.

## Routes

| Method | Path | Result |
|---|---|---|
| POST | /jobs | 202 new admission, 200 exact replay |
| GET | /jobs | Caller history, optional status/limit/cursor |
| GET | /jobs/{job_id} | Persisted state and native job ID when known |
| POST | /jobs/{job_id}/cancel | Durable intent; 202 until confirmed |
| GET | /jobs/{job_id}/logs | Launcher stdout, stderr or exit |
| GET | /usage | UTC-day jobs and allowance |

