#!/bin/bash
#
# Run this script after the project infrastructure has been created.
# This script will install and run the pipelines.
#

for i in "gcloud" "kubectl"; do
  command -v "${i}" 2>&1 > /dev/null || { echo >&2 "${i} is not installed."; echo "${MESSAGE}"; exit 1; }
done


# Set Variables
export PROJECT_ID=$(gcloud config get-value project)
source config.sh

# Submit Build
gcloud builds submit --config "app/cloudbuild.yaml"

# Open the Grafana dashboad
gcloud container clusters get-credentials cluster --region ${REGION}
unset external_ip
while [ -z $external_ip ];
  do echo "Waiting for Grafana end point ..."
    external_ip=$(kubectl get ingress grafana -n grafana -o jsonpath='{.status.loadBalancer.ingress[].ip}')
    sleep 5 
  done
echo "Grafana End point ready ... 

Please visit the FSI Pattern dashboard here: 
---
http://${external_ip}/d/9HXuXojGk/fsi-pattern
Username: ${PROJECT_ID}
Password: ${PROJECT_ID}
---

Done..."
sleep 10
open "http://${external_ip}/d/9HXuXojGk/fsi-pattern?orgId=1&refresh=1m"
