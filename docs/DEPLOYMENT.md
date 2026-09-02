# Deployment

## Prerequisites

Use an existing **Hadoop** HDInsight cluster exposing HTTPS WebHCat v1 with basic authentication. This module neither creates nor pays for a cluster. Verify MapReduce JAR support and storage access before provisioning the control plane. Spark-only endpoints are not substitutes.

Supply a VNet, a /27-or-larger integration subnet delegated to `Microsoft.App/environments`, and a separate private endpoint subnet. Both apps, HDInsight, Key Vault and the status/log storage must be reachable. Configure private DNS for the existing Key Vault and storage and permit Microsoft Entra token/JWKS endpoints and required Azure platform egress. Use the public HDInsight gateway hostname with approved network access. This module does not support custom sovereign-cloud endpoints.

The module creates private DNS zones for Blob, Queue, Cosmos and Functions. In environments that already have centrally managed zones with those names, import/adapt the resources to use your existing zones; do not create competing links for the same namespace.

