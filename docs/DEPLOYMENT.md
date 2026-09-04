# Deployment

## Prerequisites

Use an existing **Hadoop** HDInsight cluster exposing HTTPS WebHCat v1 with basic authentication. This module neither creates nor pays for a cluster. Verify MapReduce JAR support and storage access before provisioning the control plane. Spark-only endpoints are not substitutes.

Supply a VNet, a /27-or-larger integration subnet delegated to `Microsoft.App/environments`, and a separate private endpoint subnet. Both apps, HDInsight, Key Vault and the status/log storage must be reachable. Configure private DNS for the existing Key Vault and storage and permit Microsoft Entra token/JWKS endpoints and required Azure platform egress. Use the public HDInsight gateway hostname with approved network access. This module does not support custom sovereign-cloud endpoints.

The module creates private DNS zones for Blob, Queue, Cosmos and Functions. In environments that already have centrally managed zones with those names, import/adapt the resources to use your existing zones; do not create competing links for the same namespace.

## Entra registration and cluster password

Create a single-tenant API application. Set `api.requestedAccessTokenVersion` to 2, expose an API URI such as `api://CLIENT-ID`, define appropriate delegated scopes/application roles and grant callers permission. For unattended callers use an application role and admin consent. Add exact caller service-principal/user **object IDs**, not application client IDs, to profiles. Audience is the API application's client GUID. The client helper uses Azure CLI credentials after `az login`; authorize that client for the exposed delegated scope.

Place the cluster password in an existing RBAC-enabled Key Vault. `secret_id` is its versioned HTTPS secret URL; `secret_resource_id` is the corresponding unversioned ARM secret resource ID. Terraform never reads the password. Set `username` to the gateway account. Ensure the cluster can write to the chosen status prefix and that the API's new identity can read that container.

## Terraform apply

Install Terraform 1.13.5. Register Microsoft.Web, Microsoft.App, Microsoft.Storage, Microsoft.DocumentDB, Microsoft.Network, Microsoft.Insights, Microsoft.OperationalInsights, Microsoft.ManagedIdentity and Microsoft.Consumption in the subscription. Choose a Flex-compatible region with the configured ZRS/zone support.

Use a private runner with DNS/routing to the storage and Function SCM endpoints. Bootstrap a remote state account separately, disable public blob access, use Entra authentication, and grant the deployment principal Blob Data Contributor on its state container. The principal also needs resource provisioning and role-assignment rights over the target resource group, supplied subnets, existing secret scopes and log containers, plus Blob/Queue Data Contributor on the new storage accounts for Terraform data-plane operations. Use scoped rights and a separate bootstrap principal where possible.

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
cp terraform/backend.hcl.example terraform/backend.hcl
# Replace every example value and set the current month's budget start date.
terraform -chdir=terraform init -backend-config=backend.hcl
terraform -chdir=terraform plan -out=reviewed.tfplan
terraform -chdir=terraform apply reviewed.tfplan
```

Private endpoints are provisioned before storage containers and queues. DNS and role propagation can require a repeat apply after the permissions are effective. Do not turn on account keys or public networking to work around missing access.

## Publish functions

Build with `python scripts/build.py`. The explicit source directory `build/function` contains only runtime code and hashed dependencies. Flex remote build installs them. Publish both apps using Microsoft Azure Functions Core Tools v4 from that directory or the repository's manual deployment workflow. Keep APP_ROLE=api/worker as provisioned; the code indexes only the intended triggers. Do not set WEBSITE_RUN_FROM_PACKAGE or SCM_DO_BUILD_DURING_DEPLOYMENT on Flex.

