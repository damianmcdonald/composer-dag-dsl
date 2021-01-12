#!/bin/bash

###################################################################
#Script Name	  :run_flask_app.sh
#Description	  :Script file used to launch the flask app
#Args           :
#Author         :Damian McDonald
#Credits        :Damian McDonald
#License        :GPL
#Version        :1.0.0
#Maintainer     :Damian McDonald
#Status         :Development
###################################################################

export FLASK_APP=composer/api/api.py
flask run