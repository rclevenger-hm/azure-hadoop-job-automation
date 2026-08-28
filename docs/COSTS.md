# Cost controls

## What incurs cost

Flex Consumption execution and memory, Cosmos autoscale throughput and storage, eight private endpoints, DNS, queue/Blob transactions, Log Analytics ingestion and existing HDInsight nodes are separate costs. Terraform uses ZRS storage and a zonal Cosmos region; verify regional availability before applying. A running HDInsight cluster can dominate the control-plane cost even when no job is submitted.

