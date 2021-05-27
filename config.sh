# Project Constants
export REGION=${REGION:-"australia-southeast1"}
export TERRAFORM_STATE_BUCKET="terraform-state"

# Variables
export GENERATOR_TICK_HZ="10"
export LSTM_WINDOW_LENGTH="30"
export METRICS_TYPE_1_MAX_GAP_SECS="60"
export METRICS_TYPE_1_WINDOW_SECS="1"
export METRICS_TYPE_2_WINDOW_SECS="300"
export SYMBOL_TO_RUN_LSTM_ON="GBPAUD"
export RSI_LOWER_THRESHOLD="30"
export RSI_UPPER_THRESHOLD="70"

# Note that ai platform models only currently support the following regions:
# asia-northeast1, europe-west1, us-central1, us-east1, us-east4
export AI_PLATFORM_MODEL_REGION="us-east1"


# BigQuery Constants
export BIGQUERY_DATASET_NAME="forex"
export BIGQUERY_METRICS_TABLE_NAME="metrics"
export BIGQUERY_METRICS_TABLE_SCHEMA="table_schemas/metrics.json"
export BIGQUERY_PRICES_TABLE_NAME="prices"
export BIGQUERY_PRICES_TABLE_SCHEMA="table_schemas/prices.json"
export BIGQUERY_RECONERR_TABLE_NAME="reconerr"
export BIGQUERY_RECONERR_TABLE_SCHEMA="table_schemas/reconerr.json"

# GCS Constants
export GCS_BUCKET_NAME="dataflow"
export GCS_STAGING_FOLDER="staging/"
export GCS_TEMP_FOLDER="temp/"
export GCS_TFX_FOLDER="tfx/"

# GKE Constants
export GKE_CLUSTER_NAME="cluster"
export GKE_NAMESPACE_GRAFANA_NAME="grafana"
export GKE_NAMESPACE_PIPELINE_NAME="default"

# Grafana Constants
export GRAFANA_NAME="grafana"
export GRAFANA_PASSWORD=${PROJECT_ID}
export GRAFANA_USER=${PROJECT_ID}

# Pub/Sub Constants
export PUBSUB_METRICS_TOPIC="metrics"
export PUBSUB_PRICES_TOPIC="prices"
export PUBSUB_RECONERR_TOPIC="reconerr"

# Service Account Constants
export SERVICE_ACCOUNT_DATAFLOW_ACCOUNT_ID="dataflow"
export SERVICE_ACCOUNT_DATAFLOW_DISPLAY_NAME="DataFlow service account"
export SERVICE_ACCOUNT_GRAFANA_ACCOUNT_ID="grafana"
export SERVICE_ACCOUNT_GRAFANA_DISPLAY_NAME="Grafana service account"

# SQL Constants
export SQL_DATABASE_INSTANCE_NAME="database"
export SQL_DATABASE_INSTANCE_TIER="db-n1-standard-2"
export SQL_ML_METADATA_DATABASE="ml_metadata"
export SQL_ML_METADATA_USER="user"

# TFX Model Constants

# Terraform Mappings
export TF_VAR_bigquery_dataset_name=${BIGQUERY_DATASET_NAME}
export TF_VAR_bigquery_metrics_table_name=${BIGQUERY_METRICS_TABLE_NAME}
export TF_VAR_bigquery_metrics_table_schema=${BIGQUERY_METRICS_TABLE_SCHEMA}
export TF_VAR_bigquery_prices_table_name=${BIGQUERY_PRICES_TABLE_NAME}
export TF_VAR_bigquery_prices_table_schema=${BIGQUERY_PRICES_TABLE_SCHEMA}
export TF_VAR_bigquery_reconerr_table_name=${BIGQUERY_RECONERR_TABLE_NAME}
export TF_VAR_bigquery_reconerr_table_schema=${BIGQUERY_RECONERR_TABLE_SCHEMA}
export TF_VAR_gcs_bucket_name=${GCS_BUCKET_NAME}
export TF_VAR_gcs_staging_folder=${GCS_STAGING_FOLDER}
export TF_VAR_gcs_temp_folder=${GCS_TEMP_FOLDER}
export TF_VAR_gcs_tfx_folder=${GCS_TFX_FOLDER}
export TF_VAR_gcs_tfx_model=${GCS_TFX_MODEL}
export TF_VAR_gke_cluster_name=${GKE_CLUSTER_NAME}
export TF_VAR_grafana_namespace=${GKE_NAMESPACE_GRAFANA_NAME}
export TF_VAR_pipeline_namespace=${GKE_NAMESPACE_PIPELINE_NAME}
export TF_VAR_project_id=${PROJECT_ID}
export TF_VAR_pubsub_metrics_topic=${PUBSUB_METRICS_TOPIC}
export TF_VAR_pubsub_prices_topic=${PUBSUB_PRICES_TOPIC}
export TF_VAR_pubsub_reconerr_topic=${PUBSUB_RECONERR_TOPIC}
export TF_VAR_region=${REGION}
export TF_VAR_service_account_dataflow_account_id=${SERVICE_ACCOUNT_DATAFLOW_ACCOUNT_ID}
export TF_VAR_service_account_dataflow_display_name=${SERVICE_ACCOUNT_DATAFLOW_DISPLAY_NAME}
export TF_VAR_service_account_grafana_account_id=${SERVICE_ACCOUNT_GRAFANA_ACCOUNT_ID}
export TF_VAR_service_account_grafana_display_name=${SERVICE_ACCOUNT_GRAFANA_DISPLAY_NAME}
export TF_VAR_sql_database_instance_name=${SQL_DATABASE_INSTANCE_NAME}
export TF_VAR_sql_database_instance_tier=${SQL_DATABASE_INSTANCE_TIER}
export TF_VAR_sql_ml_metadata_database=${SQL_ML_METADATA_DATABASE}
export TF_VAR_sql_ml_metadata_user=${SQL_ML_METADATA_USER}
export TF_VAR_symbol_to_run_lstm_on=${SYMBOL_TO_RUN_LSTM_ON}
export TF_VAR_model_version_name=${MODEL_VERSION_NAME}
