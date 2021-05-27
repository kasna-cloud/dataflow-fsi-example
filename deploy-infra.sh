#!/bin/bash
#
# Run this script against a fresh project. This script will install all
# inrastructure required for the demo.
# Requires: gcloud
#


for i in "gcloud"; do
  command -v "${i}" 2>&1 > /dev/null || { echo >&2 "${i} is not installed."; echo "${MESSAGE}"; exit 1; }
done

# Set Variables
export PROJECT_ID=$(gcloud config get-value project)
source config.sh

# Print Help + Project Confirmation
echo "Please ensure the following before you begin:
 - You have 'gcloud' installed (https://cloud.google.com/sdk/docs/install) and authenticated (https://cloud.google.com/sdk/docs/initializing).
 - You have created a new project with billing enabled, and have permissions of 'roles/owner'.
 - You have set the project using 'gcloud config set project PROJECT_ID'."
read -n 1 -p "Deploying into PROJECT_ID: ${PROJECT_ID}, would you like to continue? (y/N) " REPLY
echo

# Check Project ID
if [[ ! ${REPLY} =~ ^[Yy]$ ]]; then
  [[ "$0" = "${BASH_SOURCE}" ]] && exit 1 || return 1
else
  # Enable Services
  gcloud services enable cloudbuild.googleapis.com

  # Set Permissions
  gcloud projects add-iam-policy-binding ${PROJECT_ID} --member serviceAccount:$(gcloud projects describe ${PROJECT_ID} --format 'value(projectNumber)')@cloudbuild.gserviceaccount.com --role roles/owner

  # Submit Build
  gcloud builds submit --config "infra/cloudbuild.yaml"
  echo "Please run the pipelines using the 'run-app.sh' script."
fi
