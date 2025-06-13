#!/bin/bash

# This script automates the process of building and deploying the backend service.
# It ensures that if any command fails, the script will exit immediately.
set -e

# This script should be run from the project root.
# It will use the configuration files located in the 'backend' directory.

echo "Building the Docker image with Cloud Build from the project root..."
echo "This will create a new image with the 'latest' tag."
gcloud builds submit --region=europe-west1 --config cloudbuild.yaml .

echo ""
echo "Deploying the new 'latest' image to Cloud Run using service.yaml..."
gcloud run services replace service.yaml --region europe-west1

echo ""
echo "✅ Deployment successful!"
echo "Your service has been updated with the latest changes." 