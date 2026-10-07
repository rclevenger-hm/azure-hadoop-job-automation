# Cost controls

## What incurs cost

Flex Consumption execution and memory, Cosmos autoscale throughput and storage, eight private endpoints, DNS, queue/Blob transactions, Log Analytics ingestion and existing HDInsight nodes are separate costs. Terraform uses ZRS storage and a zonal Cosmos region; verify regional availability before applying. A running HDInsight cluster can dominate the control-plane cost even when no job is submitted.

## Limits

Defaults: 100 admissions per caller per UTC day, 60 API requests per caller per minute, five instances per Function app, 1,000 RU/s maximum autoscale for the Cosmos container, 1 GiB/day workspace ingestion quota, 30-day terminal metadata retention. Quotas limit admissions, not a JAR's duration or compute use.

## Budget scope

The resource-group budget defaults to 150 billing-currency units/month with an 80% email threshold. It excludes preexisting HDInsight and storage in other resource groups and does not stop resources. Set a separate cluster budget and operational termination policy. Confirm pricing in the Azure calculator for your region; no cost estimate here assumes a live deployment.
