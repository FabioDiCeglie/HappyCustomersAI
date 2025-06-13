# Backend Deployment to Google Cloud Run

This document outlines the various methods to deploy the backend of the Email Support AI application to Google Cloud Run. It covers purely manual, semi-automated, and fully automated workflows.

All necessary deployment files (`Dockerfile`, `cloudbuild.yaml`, `service.yaml`, `deploy.sh`) are located in the `backend/` directory. Commands should be run from the project's root directory unless specified otherwise.

## 1. Prerequisites

- A Google Cloud Platform (GCP) project with billing enabled.
- The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` CLI) installed and authenticated.
- [Docker](https://docs.docker.com/get-docker/) installed and running on your local machine.

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

Create a Docker repository to store the container image. This only needs to be done once.
```bash
gcloud artifacts repositories create [YOUR_PROJECT_NAME] \
    --repository-format=docker \
    --location=europe-west1 \
    --description="Container images for the backend service"
```

## 4. Secret Management

Create the necessary secrets in **Secret Manager**. This is done through the Google Cloud Console. The application requires the following secrets:
- `google-api-key`
- `mongodb-url`
- `smtp-host`
- `smtp-port`
- `smtp-user`
- `smtp-password`
- `from-email`
- `from-name`

---

## Workflow 1: Manual Local Build and Deploy

This workflow uses your local machine to build and push the image. It does not use Cloud Build.

### Step 1: Build the Docker Image Locally
This command builds the image on your machine. The `-f` flag points to the Dockerfile, and `.` sets the build context to the project root (so it can find `pyproject.toml`).
```bash
docker build -t europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/[YOUR_PROJECT_NAME]/backend-image:latest -f backend/Dockerfile .
```

### Step 2: Push the Image to Artifact Registry
First, you may need to configure Docker to authenticate with Artifact Registry (one-time setup):
```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
```
Then, push the image you built:
```bash
docker push europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/[YOUR_PROJECT_NAME]/backend-image:latest
```

### Step 3: Deploy the Image Manually
This command deploys the image you just pushed. You must specify all configuration options, like secrets, as flags.
```bash
gcloud run deploy [YOUR_PROJECT_NAME] \
  --image europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/[YOUR_PROJECT_NAME]/backend-image:latest \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_API_KEY=google-api-key:latest,MONGODB_URL=mongodb-url:latest,SMTP_HOST=smtp-host:latest,SMTP_PORT=smtp-port:latest,SMTP_USER=smtp-user:latest,SMTP_PASSWORD=smtp-password:latest,FROM_EMAIL=from-email:latest,FROM_NAME=from-name:latest"
```

---

## Workflow 2: Manual Cloud Build and Deploy

This workflow uses Cloud Build to build the image in the cloud, which can be faster and doesn't require Docker locally.

### Step 1: Build the Image with Cloud Build
Because our `Dockerfile` is in a subdirectory (`backend/`), we must use a `cloudbuild.yaml` file to tell Cloud Build where to find it. This command uses that config to build the image and push it to the Artifact Registry.
```bash
gcloud builds submit --config cloudbuild.yaml .
```

### Step 2: Deploy the Image Manually
This is the same deployment command as in the previous workflow.
```bash
gcloud run deploy [YOUR_PROJECT_NAME] \
  --image europe-west1-docker.pkg.dev/[YOUR_PROJECT_ID]/[YOUR_PROJECT_NAME]/backend-image:latest \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_API_KEY=google-api-key:latest,MONGODB_URL=mongodb-url:latest,SMTP_HOST=smtp-host:latest,SMTP_PORT=smtp-port:latest,SMTP_USER=smtp-user:latest,SMTP_PASSWORD=smtp-password:latest,FROM_EMAIL=from-email:latest,FROM_NAME=from-name:latest"
```

---

## Workflow 3: Declarative Deployment with `service.yaml` (IaC)

This is a more robust approach using the principles of **Infrastructure as Code (IaC)**. The `service.yaml` file acts as the single source of truth for your service's configuration.

### Step 1: Create the `service.yaml` File
You only need to do this once to get started.

*   **Option A (Recommended): Generate from an existing service.**
    If you've already deployed using a previous workflow, you can create a perfect YAML file from it.
    ```bash
    gcloud run services describe [YOUR_PROJECT_NAME] --region europe-west1 --format=export > backend/service.yaml
    ```
*   **Option B: Write it from scratch.**
    You can also author the `backend/service.yaml` file manually.

### Step 2: Build the Image
The image must still be built and pushed to the registry first (using either local Docker or Cloud Build).
```bash
gcloud builds submit --config cloudbuild.yaml .
```

### Step 3: Deploy Using the YAML file
This command creates or updates the Cloud Run service to match the state defined in your YAML file.
```bash
gcloud run services replace backend/service.yaml --region europe-west1
```

---

## Workflow 4: Automated Deployment with a Script (Recommended)

This is the simplest and most repeatable workflow. The `deploy.sh` script combines the Cloud Build and declarative deployment steps into a single command.

### Run the Script
From the project **root directory**, simply execute the script:
```bash
./backend/deploy.sh
```
This script will first build the image (using `cloudbuild.yaml`) and then deploy it (using `service.yaml`).

---

## Appendix: Service Account Permissions

The Cloud Run service uses a service account to interact with other Google Cloud services. To access secrets, this account needs the **Secret Manager Secret Accessor** role. The service account ID typically follows the format `[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`. This permission can be granted in the IAM or Secret Manager pages of the Cloud Console.