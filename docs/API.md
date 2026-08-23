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

## Submission contract

Required fields are profile plus jar_path, job_class, input_path and output_path. Optional arguments is an array of at most 20 strings, each at most 1,024 characters. Input and output must differ. Paths must be under configured canonical directory prefixes. Accepted URI schemes are abfss, wasbs and hdfs. The whole JSON body is limited to 64 KiB and combined program strings to 10,240 characters. No unknown fields are accepted.

An Idempotency-Key of 8–128 letters, digits, dots, underscores, colons or hyphens is required. Keep it stable when the API response is lost. A key reused with different inputs returns 409. Never use a new key to work around an ambiguous remote outcome. Quotas count admissions even if a job subsequently fails or is cancelled.

## Status and cancellation

The API returns persisted state, not a synchronous gateway poll. The timer refreshes asynchronously, usually after the 120-second poll lease. A cancel acknowledgment means the request was accepted, not that execution stopped. NEEDS_REVIEW is an operator state and can coexist with remote activity. See ARCHITECTURE.md for transitions.

## History and logs

History returns at most 100 records, default 20. Cursors are bound to caller and status filter; reuse them unchanged. Records expire after configured terminal retention. Logs select stdout, stderr or exit and read from byte zero, default 16 KiB and maximum 64 KiB. A truncated flag indicates more data. These are launcher files, not all Hadoop task logs. Missing uploads return 404; jobs with unknown native identity return 409.

## Errors

Structured errors contain code, error and request_id. 400 denotes validation, 401 authentication, 403 profile/path authorization, 404 missing resources, 409 state/idempotency conflict, 413 oversized body, 415 content type, 429 quota and 503 dependency failure. Retry-After accompanies throttling; daily quota waits until UTC midnight. Responses contain no-store and X-Request-Id. Internal dependency details stay out of the response.
