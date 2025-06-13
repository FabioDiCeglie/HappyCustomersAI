# Backend Deployment to Google Cloud Run

This document outlines the steps taken to deploy the backend of the Email Support AI application to Google Cloud Run.

## 1. Prerequisites

- A Google Cloud Platform (GCP) project with billing enabled.
- The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` CLI) installed and authenticated.

## 2. Initial Setup

1.  **Set the active GCP project:**
    ```bash
    gcloud config set project [YOUR_PROJECT_ID]
    ```

2.  **Enable necessary APIs:**
    ```bash
    gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
    ```

## 3. Artifact Registry Setup

1.  **Create a Docker repository to store the container image:**
    ```bash
    gcloud artifacts repositories create happy-customers-ai-backend \
        --repository-format=docker \
        --location=europe-west1 \
        --description="Happy Customers AI Backend Repository"
    ```

## 4. Building the Docker Image

1.  **Create a `cloudbuild.yaml` file** to define the build steps, as the `Dockerfile` is located in a subdirectory:
    ```yaml
    steps:
    - name: 'gcr.io/cloud-builders/docker'
      args: ['build', '-t', 'europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/happy-customers-ai-backend/backend-image:latest', '-f', 'backend/Dockerfile', '.']
    images:
    - 'europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/happy-customers-ai-backend/backend-image:latest'
    ```

2.  **Submit the build to Google Cloud Build:**
    ```bash
    gcloud builds submit --region=europe-west1 --config cloudbuild.yaml .
    ```

## 5. Secret Management

1.  **Create secrets in Secret Manager** for each environment variable required by the application. This is done through the Google Cloud Console.

    The following secrets were created:
    - `mongodb-url`
    - `smtp-host`
    - `smtp-port`
    - `smtp-user`
    - `smtp-password`
    - `from-email`
    - `from-name`

## 6. Deployment to Cloud Run

1.  **Deploy the container image to Cloud Run**, making it publicly accessible and injecting the secrets as environment variables:
    ```bash
    gcloud run deploy happy-customers-ai-backend \
        --image europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/happy-customers-ai-backend/backend-image:latest \
        --region europe-west1 \
        --allow-unauthenticated \
        --set-secrets="MONGODB_URL=mongodb-url:latest,SMTP_HOST=smtp-host:latest,SMTP_PORT=smtp-port:latest,SMTP_USER=smtp-user:latest,SMTP_PASSWORD=smtp-password:latest,FROM_EMAIL=from-email:latest,FROM_NAME=from-name:latest"
    ```