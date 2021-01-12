#!/bin/bash

###################################################################
#Script Name	  :run_container.sh
#Description	  :Script used to run the composer-dag-dsl container
#Args           :
#Author         :Damian McDonald
#Credits        :Damian McDonald
#License        :GPL
#Version        :1.0.0
#Maintainer     :Damian McDonald
#Status         :Development
###################################################################

DOCKER_TAG=composer-dag-dsl:1.0.0

docker run -p 80:80 --env-file=env_composer composer-dag-dsl:1.0.0