# Infra Components
This directory contains infrastructure components which are used by the real-time and training jobs. These components are:
* GCS buckets
* BigQuery dataset and tables - these are defined in the [table_schemas](./table_schemas) directory and used by the Grafana dashboards and Dataflow piplines.
* GKE Cluster to host:
    * Training cronjob
    * Pipeline deployments
    * FOREXGenerator
    * Grafana dashboard engine
* Service Account and IAM bindings
* Cloud SQL database for TFX model training

Please see the [CloudBuild](./cloudbuild.yaml) and [Terraform](./main.tf) for what is deployed. 

