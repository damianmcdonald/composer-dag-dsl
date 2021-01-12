#!/usr/bin/env python

"""auth_service.py: Service module that provides functionalities related to GCP authentication"""

__author__ = "Damian McDonald"
__credits__ = ["Damian McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Damian McDonald"
__status__ = "Development"

import os
import json
import base64
import logging
import google.auth
from google.oauth2 import service_account
from composer.utils import log_service

# GCP URLs for IAM scope and OAUTH tokens
IAM_SCOPE = 'https://www.googleapis.com/auth/iam'
OAUTH_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'

# The URL that provides public certificates for verifying ID tokens issued
# by Google's OAuth 2.0 authorization server.
_GOOGLE_OAUTH2_CERTS_URL = "https://www.googleapis.com/oauth2/v1/certs"

# The URL that provides public certificates for verifying ID tokens issued
# by Firebase and the Google APIs infrastructure
_GOOGLE_APIS_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509"
    "/securetoken@system.gserviceaccount.com"
)

# Scope definitions for google authentication issuer
_GOOGLE_ISSUERS = ["accounts.google.com", "https://accounts.google.com"]

# gets the logger for this module
logger = log_service.get_module_logger(__name__)


# [START __get_composer_environment]
def get_authenticated_session():
    """
    Gets an authenticated GCP session based on a GCP service account.
    Returns:
        a validated instance of google.auth.transport.requests.AuthorizedSession
    """
    logger.log(logging.DEBUG, "Getting an authenticated GCP session")
    credentials = get_credentials()
    authed_session = google.auth.transport.requests.AuthorizedSession(credentials)
    return authed_session
# [END __get_composer_environment]


# [START get_credentials]
def get_credentials():
    """
    Gets the credentials for and authenticated GCP session based on a GCP service account.
    Returns:
        an instance of google.oauth2.service_account.Credentials
    """
    logger.log(logging.DEBUG, "Getting the GCP credentials")
    # if a service account is explicitly defined, use that for authentication
    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        service_account_info = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        logger.log(
            logging.DEBUG,
            f"GOOGLE_APPLICATION_CREDENTIALS env var is defined, using service account for authentication"
        )

        # the service account is base64 encoded json, we need to decode it and read the json
        service_account_info = json.loads(base64.b64decode(service_account_info).decode("utf-8"))

        # Authenticate with Google Cloud.
        # See: https://cloud.google.com/docs/authentication/getting-started
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        return credentials

    # if a service account is not explicitly defined, use default authentication
    logger.log(
        logging.DEBUG,
        f"GOOGLE_APPLICATION_CREDENTIALS env var is not defined, using default auth mechanism"
    )
    # if no service account is explicitly defined, use default auth
    credentials, _ = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    return credentials
# [END get_credentials]


# [START get_id_token]
def get_id_token(request, audience):
    """
    Gets the OAUTH id token for an authenticated GCP session based on a GCP service account.
    Returns:
        an instance of google.oauth2.service_account.IDTokenCredentials.token
    """
    logger.log(logging.DEBUG, "Getting a GCP OAUTH id token")
    # if a service account is explicitly defined, use that for authentication
    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        service_account_info = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        logger.log(
            logging.DEBUG,
            f"GOOGLE_APPLICATION_CREDENTIALS env var is defined, using service account for authentication"
        )

        service_account_info = json.loads(base64.b64decode(service_account_info).decode("utf-8"))
        credentials = service_account.IDTokenCredentials.from_service_account_info(
            service_account_info,
            target_audience=audience
        )
        credentials.refresh(request)
        return credentials.token

    return None
# [END get_id_token]
