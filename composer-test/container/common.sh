#!/bin/bash

###################################################################
#Script Name	  :common.sh
#Description	  :Common script that defines variables and functions used by other scripts
#Args           :
#Author         :Damian McDonald
#Credits        :Damian McDonald
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

# define the api end point of the service to be tested
REST_URL=https://composer-service-wqi5tzidoa-ey.a.run.app/api/v1

# relative path of a valid json payload
JSON_PAYLOAD=payloads/minimal_dag_kubernetes_pod_operator.json

# name of the dag file
DAG_NAME="minimal_dag_kubernetes_pod_operator"