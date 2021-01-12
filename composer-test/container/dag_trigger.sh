#!/bin/bash

###################################################################
#Script Name	  :dag_trigger.sh
#Description	  :Script used to test the /api/v1/dag/trigger/<dag_name> REST API method
#Args           :
#Author         :Damian McDonald
#Credits        :Damian McDonald
#License        :GPL
#Version        :1.0.0
#Maintainer     :Damian McDonald
#Status         :Development
###################################################################

# import the common libs, variables
source common.sh

echo -e "Executing REST API request: ${GREEN}${REST_URL}/dag/trigger/${DAG_NAME}${NC}"
echo ""

JSON_RESPONSE=$(curl --request PUT ${REST_URL}/dag/trigger/${DAG_NAME})

echo ""
echo "Request response presented below"
echo ""

echo "${JSON_RESPONSE}" | jq .