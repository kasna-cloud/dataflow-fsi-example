# Create BigQuery Datasets + Tables
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.bigquery_dataset_name
  location   = var.region
  project    = var.project_id
}

resource "google_bigquery_table" "metrics" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  project    = var.project_id
  schema     = file(var.bigquery_metrics_table_schema)
  table_id   = var.bigquery_metrics_table_name
}

resource "google_bigquery_table" "prices" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  project    = var.project_id
  schema     = file(var.bigquery_prices_table_schema)
  table_id   = var.bigquery_prices_table_name
}

resource "google_bigquery_table" "reconerr" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  project    = var.project_id
  schema     = file(var.bigquery_reconerr_table_schema)
  table_id   = var.bigquery_reconerr_table_name
}

# Create GCS Buckets + Objects
resource "google_storage_bucket" "bucket" {
  uniform_bucket_level_access = true
  project                     = var.project_id
  name                        = "${var.project_id}_${var.gcs_bucket_name}"
  location                    = var.region
  force_destroy               = true
}

resource "google_storage_bucket_object" "staging_folder" {
  bucket  = google_storage_bucket.bucket.name
  content = "This is the staging area for dataflow jobs - do not delete the folder!"
  name    = "${var.gcs_staging_folder}README.txt"
}

resource "google_storage_bucket_object" "temp_folder" {
  bucket  = google_storage_bucket.bucket.name
  content = "This is the temp area for dataflow jobs - do not delete the folder!"
  name    = "${var.gcs_temp_folder}README.txt"
}

resource "google_storage_bucket_object" "tfx_folder" {
  bucket  = google_storage_bucket.bucket.name
  content = "This is the tfx area for dataflow jobs - do not delete the folder!"
  name    = "${var.gcs_tfx_folder}README.txt"
}

# Create GKE
resource "google_container_cluster" "cluster" {
  enable_autopilot = true
  location         = var.region
  name             = var.gke_cluster_name
  project          = var.project_id
  
  # WORKAROUND for https://github.com/hashicorp/terraform-provider-google/issues/10782
  ip_allocation_policy { }

  depends_on = [
    google_project_service.container
  ]
}

# Create Google Project Services
resource "google_project_service" "aiplatform" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "aiplatform.googleapis.com"
}

resource "google_project_service" "bigquery" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "bigquery.googleapis.com"
}

resource "google_project_service" "container" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "container.googleapis.com"
}

resource "google_project_service" "dataflow" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "dataflow.googleapis.com"
}

resource "google_project_service" "iam" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "iam.googleapis.com"
}

resource "google_project_service" "ml" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "ml.googleapis.com"
}

resource "google_project_service" "sqladmin" {
  disable_dependent_services = true
  project                    = var.project_id
  service                    = "sqladmin.googleapis.com"
}

# Create Pub/Sub
resource "google_pubsub_topic" "metrics" {
  name    = var.pubsub_metrics_topic
  project = var.project_id
}

resource "google_pubsub_topic" "prices" {
  name    = var.pubsub_prices_topic
  project = var.project_id
}

resource "google_pubsub_topic" "reconerr" {
  name    = var.pubsub_reconerr_topic
  project = var.project_id
}

# Create Service Accounts + Google Project IAM Members + Service Account IAM Bindings
resource "google_project_iam_member" "dataflow_bigquery_dataowner" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/bigquery.dataOwner"
}

resource "google_project_iam_member" "dataflow_bigquery_jobuser" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/bigquery.jobUser"
}

resource "google_project_iam_member" "dataflow_cloudsql_client" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/cloudsql.client"
}

resource "google_project_iam_member" "dataflow_dataflow_admin" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/dataflow.admin"
}

resource "google_project_iam_member" "dataflow_dataflow_worker" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/dataflow.worker"
}

resource "google_project_iam_member" "dataflow_service_account_user" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
}

resource "google_project_iam_member" "dataflow_ml_developer" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/ml.developer"
}

resource "google_project_iam_member" "dataflow_pubsub_publisher" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/pubsub.publisher"
}

resource "google_project_iam_member" "dataflow_storage_objectadmin" {
  member  = local.dataflow_service_account
  project = var.project_id
  role    = "roles/storage.objectAdmin"
}

resource "google_project_iam_member" "grafana_bigquery_dataviewer" {
  member  = local.grafana_service_account
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
}

resource "google_project_iam_member" "grafana_bigquery_jobuser" {
  member  = local.grafana_service_account
  project = var.project_id
  role    = "roles/bigquery.jobUser"
}

resource "google_service_account" "dataflow" {
  account_id   = var.service_account_dataflow_account_id
  display_name = var.service_account_dataflow_display_name
  project      = var.project_id

  depends_on = [
    google_project_service.iam
  ]
}

resource "google_service_account" "grafana" {
  account_id   = var.service_account_grafana_account_id
  display_name = var.service_account_grafana_display_name
  project      = var.project_id

  depends_on = [
    google_project_service.iam
  ]
}

resource "google_service_account_iam_binding" "dataflow_iam_workloadidentityuser" {
  members            = local.dataflow_service_account_members
  role               = "roles/iam.workloadIdentityUser"
  service_account_id = google_service_account.dataflow.name

  depends_on = [
    google_container_cluster.cluster
  ]
}

resource "google_service_account_iam_binding" "grafana_iam_workloadidentityuser" {
  members            = local.grafana_service_account_members
  role               = "roles/iam.workloadIdentityUser"
  service_account_id = google_service_account.grafana.name

  depends_on = [
    google_container_cluster.cluster
  ]
}

resource "google_service_account_key" "bigquery" {
  service_account_id = google_service_account.grafana.name
}

# Create SQL
resource "google_sql_database_instance" "instance" {
  deletion_protection = "true"
  region              = var.region
  name                = var.sql_database_instance_name
  project             = var.project_id
  database_version    = "MYSQL_5_6"

  depends_on = [
    google_project_service.sqladmin
  ]

  settings {
    tier = var.sql_database_instance_tier
  }
}

resource "google_sql_database" "database" {
  instance = google_sql_database_instance.instance.name
  name     = var.sql_ml_metadata_database
  project  = var.project_id
}

resource "google_sql_user" "user" {
  host     = "%"
  instance = google_sql_database_instance.instance.name
  name     = var.sql_ml_metadata_user
  project  = var.project_id
}
