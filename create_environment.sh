#!/bin/bash

###################################################################
#Script Name    :create_environment.sh
#Description    :Script that creates Composer, Cloud Run, Container Registry enviroments
#Args           :
#Author         :Damian McDonald
#License        :GPL
#Version        :1.0.0
#Maintainer     :Damian McDonald
#Status         :Development
###################################################################

# define console colours
RED='\033[0;31m'
BLACK='\033[0;30m'
GREEN='\033[0;32m'
BROWN='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${GREEN} ,-----.                                                          ,---.  ,------. ,--."
echo -e "${GREEN}'  .--./ ,---. ,--,--,--. ,---.  ,---.  ,---.  ,---. ,--.--.     /  O  \ |  .--. '|  |"
echo -e "${GREEN}|  |    | .-. ||        || .-. || .-. |(  .-' | .-. :|  .--'    |  .-.  ||  '--' ||  |"
echo -e "${GREEN}'  '--' ' '-' '|  |  |  || '-' '' '-' '.-'  ) |   --.|  |       |  | |  ||  | --' |  |"
echo -e "${GREEN} '-----' '---' '--'--'--'|  |-'  '---' '----'  '----''--'       '--' '--''--'     '--'"
echo -e "${GREEN}                         '--'                                                         "

echo -e "${NC}"

# define global variables
# set the project id manually: gcloud config set project ${GCP_PROJECT_ID}
GCP_PROJECT_ID=$(gcloud config get-value project 2> /dev/null)
GCP_LOCATION=europe-west1

# composer variables
COMPOSER_NAME=composer
COMPOSER_IMAGE_VER=composer-1.13.4-airflow-1.10.12
COMPOSER_AIRFLOW_CONFIGS=api-auth_backend=airflow.api.auth.backend.default

# container registry variables
GIT_SOURCE_URL=https://github.com/damianmcdonald/composer-dag-dsl.git
DOCKER_IMAGE=eu.gcr.io/<GCP_PROJECT_ID>/composer-dag-dsl:1.0.0

# cloud run variables
CLOUD_RUN_SERVICE_ACCOUNT_NAME=composer-api
CLOUD_RUN_SERVICE_ACCOUNT_ID=${CLOUD_RUN_SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com
CLOUD_RUN_NAME=composer-api
CLOUD_RUN_MEMORY=512Mi
CLOUD_RUN_ENV_VARS=PYTHONPATH=/app,LOG_LEVEL=DEBUG,GIT_PYTHON_GIT_EXECUTABLE=/usr/bin/git,GUNICORN_PORT=80,GUNICORN_WORKERS=2,PROJECT_ID=${GCP_PROJECT_ID},GCP_LOCATION=${GCP_LOCATION},COMPOSER_ENVIRONMENT=${COMPOSER_NAME}

# enable the relevant apis
echo -e "Enabling the following APIs"

echo -e "Enabling: ${YELLOW}Cloud Composer API${NC}"
gcloud services enable composer.googleapis.com

echo -e "Enabling: ${YELLOW}Cloud Run API${NC}"
gcloud services enable run.googleapis.com

echo -e "Enabling: ${YELLOW}Container Registry API${NC}"
gcloud services enable containerregistry.googleapis.com

echo -e "${NC}"

# create the composer environment
# see https://cloud.google.com/sdk/gcloud/reference/composer/environments/create
echo -e "Creating a Cloud Composer environment with the following settings:"
echo -e "GCP Project Id: ${BLUE}${GCP_PROJECT_ID}${NC}"
echo -e "GCP Location: ${BLUE}${GCP_LOCATION}${NC}"
echo -e "Composer Name: ${BLUE}${COMPOSER_NAME}${NC}"
echo -e "Composer Image Version: ${BLUE}${COMPOSER_IMAGE_VER}${NC}"
echo -e "Additional Airflow Configs: ${BLUE}${COMPOSER_AIRFLOW_CONFIGS}${NC}"

echo -e "${NC}"

gcloud composer environments create ${COMPOSER_NAME} \
--location=${GCP_LOCATION} \
--python-version=3 \
--image-version=${COMPOSER_IMAGE_VER} \
--airflow-configs=${COMPOSER_AIRFLOW_CONFIGS} \
--async

echo -e "The Cloud Composer environment is now being created in the background."
echo -e "${YELLOW}COFFEE TIME!!!${NC}This can take up to 50 minutes."

echo -e "${NC}"

# download the source code, build docker image and push to container registry
echo -e "Grabbing the project source code."
if [ -d "composer-api-src" ]; then rm -rvf "composer-api-src"; fi
git clone ${GIT_SOURCE_URL} composer-api-src
cd composer-api-src

echo -e "${NC}"

# add GCP Cloud Registry as a Docker creds helper 
echo -e "Configure Docker to push to ${BLUE}eu.gcr.io${NC}."
gcloud auth configure-docker "eu.gcr.io"

# build and tag the Docker image
echo -e "Building and tagging the image."
docker build -t ${DOCKER_IMAGE} .

# push the tagged image from local registry to GCP Cloud Registry
echo -e "Pushing the image to Container Registry: ${YELLOW}${DOCKER_IMAGE}${NC}."
docker push ${DOCKER_IMAGE}

echo -e "${NC}"

cd ..

# create the service account to be used with Cloud Run
# see https://cloud.google.com/iam/docs/creating-managing-service-accounts
echo -e "Creating the service account for Cloud Run"
gcloud iam service-accounts create ${CLOUD_RUN_SERVICE_ACCOUNT_NAME} \
    --description="Used for connecting the Cloud Run composer api to Cloud Composer" \
    --display-name="Composer API Service Account"

# grant the roles on the service account
echo -e "Granting roles for the service account for ${CLOUD_RUN_SERVICE_ACCOUNT_ID}"
echo -e "Granting role: ${YELLOW}roles/iam.serviceAccountUser${NC}"
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SERVICE_ACCOUNT_ID}" \
    --role="roles/iam.serviceAccountUser"

echo -e "Granting role: ${YELLOW}roles/project.Owner${NC}"
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SERVICE_ACCOUNT_ID}" \
    --role="roles/owner"

echo -e "Granting role: ${YELLOW}roles/iam.serviceAccountTokenCreator${NC}"
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${CLOUD_RUN_SERVICE_ACCOUNT_ID}" \
    --role="roles/iam.serviceAccountTokenCreator"

echo -e "Lisiting the service account roles:"
gcloud projects get-iam-policy ${GCP_PROJECT_ID}  \
--flatten="bindings[].members" \
--format='table(bindings.role)' \
--filter="bindings.members:${CLOUD_RUN_SERVICE_ACCOUNT_ID}"

echo -e "${NC}"

# deploy the cloud run container
# see https://cloud.google.com/sdk/gcloud/reference/run/deploy
echo -e "Deploying the cloud run container with the following details:"
echo -e "Cloud Run Service Name: ${YELLOW}${CLOUD_RUN_NAME}${NC}"
echo -e "Cloud Run Image Name: ${YELLOW}${DOCKER_IMAGE}${NC}"
echo -e "Cloud Run Memory Allocation: ${YELLOW}${CLOUD_RUN_MEMORY}${NC}"
gcloud run deploy ${CLOUD_RUN_NAME} \
--image=${DOCKER_IMAGE} --memory=${CLOUD_RUN_MEMORY} \
--service-account=${CLOUD_RUN_SERVICE_ACCOUNT_ID} \
--set-env-vars=${CLOUD_RUN_ENV_VARS} --port=80 \
--allow-unauthenticated --platform=managed --region=${GCP_LOCATION} --async

echo -e "${NC}"

echo -e "The Cloud Run environment is now being created in the background."

echo -e "${NC}"

echo -e "${GREEN}DEPLOYMENT PROCESS COMPLETE!!!${NC}"

echo -e "${NC}"

echo -e "Now you should navigate to the GCP Console and check the status of the Composer and Cloud Run deployments."