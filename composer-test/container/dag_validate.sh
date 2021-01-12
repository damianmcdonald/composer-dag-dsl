#!/bin/bash

###################################################################
#Script Name	  :dag_validate.sh
#Description	  :Script used to test the /api/v1/dag/validate REST API method
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

echo -e "Executing REST API request: ${GREEN}${REST_URL}/dag/validate${NC}"
echo ""

JSON_RESPONSE=$(curl --header "Content-Type: application/json" \
  --request POST \
  --data @${JSON_PAYLOAD} \
  ${REST_URL}/dag/validate)

echo ""
echo "Request response presented below"
echo ""

echo "${JSON_RESPONSE}" | jq .