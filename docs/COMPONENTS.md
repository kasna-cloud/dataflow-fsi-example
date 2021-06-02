# Components
## Design Principles

The key design principles used in the creation of this example are:
- Keep data unobfuscated between components to ease inspection and increase flexibility
- Ensure consistency in data by using a shared module for all transformations
- Use managed services, minimise infrastructure management overheads
- Ensure hermetic seal code paths between training and inference pipelines, the code in our example is shared between training and inference

## Components 

This example can be thought of in two distinct, logical functions. One for real-time ingestion of prices and determination of RSI presence, and another for the re-training of the model to improve prediction.

The logical diagram for the real-time and training in GCP components is below.

![Logical diagram](./docs/Dataflow-FSI-Example-Logical.png)

### Storage Components
* Three PubSub Topics: prices, metrics, and reconerr
* One BigQuery Dataset with 3 Tables: 
    * prices
    * metrics
    * reconerr
* One AI Platform Model
* One Cloud SQL Database for ML Metadata

### Compute Components
* Autopilot GKE Cluster: 
    * price generator deployment
    * grafana deployment
    * tfx retraining pipeline cron job, and a singleton job to start dataflow streaming pipelines
* Dataflow streaming pipelines:
    * Metrics Library (Java) 
    * Inference Pipeline (Python)
    * 3x PubSub-to-BigQuery Pipelines (Python)
* Dataflow batch pipline:
    * Re-training pipeline created dynamically by TFX when the GKE cronjob is run (every hour)


## Cloud Builds
`deploy_infra.sh`: deploy storage components, deploy GKE, enable APIS, create service accounts
`run_app.sh`: deploy metrics dataflow pipeline (java), deploy kubernetes resources
