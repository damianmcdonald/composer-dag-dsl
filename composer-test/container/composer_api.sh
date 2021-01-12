#!/bin/bash

###################################################################
#Script Name	  :composer_api.sh
#Description	  :Script used to test the /api/v1/composer/api REST API method
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

echo -e "Executing REST API request: ${GREEN}${REST_URL}/composer/api${NC}"
echo ""

JSON_RESPONSE=$(curl --request GET ${REST_URL}/composer/api)

echo ""
echo "Request response presented below"
echo ""

echo "${JSON_RESPONSE}" | jq .