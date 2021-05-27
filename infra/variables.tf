# Project Constants
variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

# BigQuery Constants
variable "bigquery_dataset_name" {
  type = string
}

variable "bigquery_metrics_table_name" {
  type = string
}

variable "bigquery_metrics_table_schema" {
  type = string
}

variable "bigquery_prices_table_name" {
  type = string
}

variable "bigquery_prices_table_schema" {
  type = string
}

variable "bigquery_reconerr_table_name" {
  type = string
}

variable "bigquery_reconerr_table_schema" {
  type = string
}

# GCS Constants
variable "gcs_bucket_name" {
  type = string
}

variable "gcs_staging_folder" {
  type = string
}

variable "gcs_temp_folder" {
  type = string
}

variable "gcs_tfx_folder" {
  type = string
}

# GKE Constants
variable "gke_cluster_name" {
  type = string
}

# Pub/Sub Constants
variable "pubsub_metrics_topic" {
  type = string
}

variable "pubsub_prices_topic" {
  type = string
}

variable "pubsub_reconerr_topic" {
  type = string
}

# Service Account Constants
locals {
  dataflow_service_account = "serviceAccount:${google_service_account.dataflow.email}"

  dataflow_service_account_members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${var.pipeline_namespace}/${var.service_account_dataflow_account_id}]"
  ]

  grafana_service_account = "serviceAccount:${google_service_account.grafana.email}"

  grafana_service_account_members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${var.grafana_namespace}/${var.service_account_grafana_account_id}]"
  ]
}

variable "pipeline_namespace" {
  type = string
}

variable "grafana_namespace" {
  type = string
}

variable "service_account_dataflow_account_id" {
  type = string
}

variable "service_account_dataflow_display_name" {
  type = string
}

variable "service_account_grafana_account_id" {
  type = string
}

variable "service_account_grafana_display_name" {
  type = string
}

# SQL Constants
variable "sql_database_instance_name" {
  type = string
}

variable "sql_database_instance_tier" {
  type = string
}

variable "sql_ml_metadata_database" {
  type = string
}

variable "sql_ml_metadata_user" {
  type = string
}
