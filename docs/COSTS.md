# Cost controls

## What incurs cost

Flex Consumption execution and memory, Cosmos autoscale throughput and storage, eight private endpoints, DNS, queue/Blob transactions, Log Analytics ingestion and existing HDInsight nodes are separate costs. Terraform uses ZRS storage and a zonal Cosmos region; verify regional availability before applying. A running HDInsight cluster can dominate the control-plane cost even when no job is submitted.

## Limits

Defaults: 100 admissions per caller per UTC day, 60 API requests per caller per minute, five instances per Function app, 1,000 RU/s maximum autoscale for the Cosmos container, 1 GiB/day workspace ingestion quota, 30-day terminal metadata retention. Quotas limit admissions, not a JAR's duration or compute use.

