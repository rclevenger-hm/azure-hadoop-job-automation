# Capability comparison

Reference snapshots inspected on 2026-10-07: [OCI](https://github.com/rclevenger-hm/oci-hadoop-job-automation) at `af9ac91b845aa1b8b709d1fdf74b58dc3cdeadde`, [AWS](https://github.com/rclevenger-hm/aws-hadoop-job-automation) at `63b7daf05cd453cb9d800b092453f17eb7fc03fd`, and [GCP](https://github.com/rclevenger-hm/gcp-hadoop-job-automation) at `a95e3fa4597aadd8ad1e6d3e434c6d1c4af2e990`.

| Capability | OCI baseline | AWS / GCP | Azure implementation |
|---|---|---|---|
| Hadoop JAR / MapReduce | SSH command | EMR steps / Dataproc Hadoop jobs | HDInsight WebHCat MapReduce |
| Four original request fields | Yes | Yes, with profile | Yes, with profile |
| Async durable state | No | Yes | Cosmos DB + queue + timer |
| Ownership and history | No durable history | Per caller | Verified Entra object ID |
| Quotas and idempotency | No | Transactional | Same-partition Cosmos transaction |
| Cancellation | No endpoint | Native service API | WebHCat DELETE, observed completion |
| Unknown submission | Manual inspection | Reconcile native identity | Scan and verify owner + all inputs + random statusdir |
| Logs | Bounded synchronous streams | Archived step / driver logs | Bounded launcher stdout, stderr, exit |
| Infrastructure | Function setup guidance | Terraform control plane | Private Functions, queue, Cosmos, identity, alerts, budget |

## Differences that matter

This is functional parity for native Hadoop submission, not a claim that cloud services are identical. GCP has a native request UUID and supports bounded safe retries; WebHCat has no idempotency token, so Azure deliberately never repeats a claimed POST. Launcher logs do not include all YARN task logs, EMR controller logs, or Dataproc driver segments. Operators can use cluster-native tooling for full task diagnostics. Arbitrary JARs remain trusted code with the cluster account's storage permissions.

The Azure design improves on the synchronous OCI baseline with durable long-running job management, managed control-plane credentials, per-caller admission controls and recovery. Live-cluster parity requires the documented Azure acceptance tests.
