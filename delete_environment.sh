#!/bin/bash

###################################################################
#Script Name    :delete_environment.sh
#Description    :Script that deletes Composer, Cloud Run, Container Registry enviroments
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

# define global variables
# set the project id manually: gcloud config set project ${GCP_PROJECT_ID}
GCP_PROJECT_ID=$(gcloud config get-value project 2> /dev/null)
GCP_LOCATION=europe-west1

# composer environment to delete
COMPOSER_NAME=composer

# cloud run and service account to delete
CLOUD_RUN_SERVICE_ACCOUNT_NAME=composer-api
CLOUD_RUN_SERVICE_ACCOUNT_ID=${CLOUD_RUN_SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com
CLOUD_RUN_NAME=composer-api

# container registry image to delete
DOCKER_IMAGE=eu.gcr.io/<GCP_PROJECT_ID>/composer-dag-dsl:1.0.0

# delete the local git repo
echo -e "Deleting the local source repository: ${RED}composer-api-src${NC}"
if [ -d "composer-api-src" ]; then rm -rvf "composer-api-src"; fi

echo -e "${NC}"

# delete the composer environment
echo -e "Deleting the Cloud Composer environment: ${RED}${COMPOSER_NAME}${NC}"
gcloud composer environments delete ${COMPOSER_NAME} --location ${GCP_LOCATION}

echo -e "${NC}"

# delete the cloud run service
echo -e "Deleting the Cloud Run environment: ${RED}${CLOUD_RUN_NAME}${NC}"
gcloud beta run services delete ${CLOUD_RUN_NAME} --platform managed --region ${GCP_LOCATION}

echo -e "${NC}"

# delete the container registry image
echo -e "Deleting the Container Registry image: ${RED}${DOCKER_IMAGE}${NC}"
gcloud container images delete ${DOCKER_IMAGE} --force-delete-tags

# delete the service account
echo -e "Deleting the service account: ${CLOUD_RUN_SERVICE_ACCOUNT_ID}"
gcloud iam service-accounts delete ${CLOUD_RUN_SERVICE_ACCOUNT_ID}

echo -e "${NC}"

echo -e "${GREEN}CLEANUP PROCESS COMPLETE!!!${NC}"

echo -e "${NC}"

echo -e "If the commands above executed without errors then the resources have been cleaned up."