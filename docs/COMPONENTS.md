## Components:

Storage Components:
* Three PubSub Topics: prices, metrics, and reconerr
* One BigQuery Dataset with 3 Tables: prices, metrics, and reconerr
* One AI Platform Model
* One Cloud SQL Database for ML Metadata

Compute Components:
* Metrics Library Dataflow Pipeline (Java)
* GKE Cluster: price generator deployment, grafana deployment, tfx retraining pipeline cron job, and a singleton job to start dataflow streaming pipelines:
    * Dataflow Streaming Pipelines: Inference Pipeline (Python), 3x PubSub-to-BigQuery Pipelines (Python)
    * Dataflow Batch Pipelines: Created dynamically by TFX when the GKE cronjob is ran (every hour)

Cloud Builds:
`deploy_infra.sh`: deploy storage components, deploy GKE, enable APIS, create service accounts
`run_app.sh`: deploy metrics dataflow pipeline (java), deploy kubernetes resources