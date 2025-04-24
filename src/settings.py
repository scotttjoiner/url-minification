# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

import os

# Flask settings
FLASK_SERVER_NAME = 'localhost:8888'
FLASK_PORT = os.environ.get('FLASK_PORT') or 8888

# Do not use debug mode in production
FLASK_DEBUG = True if os.environ.get('FLASK_DEBUG') is None else os.environ['FLASK_DEBUG']  

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False
RESTPLUS_ERROR_404_HELP = False

# Mongo settings
MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/urls_web'

# OAUTH settings
IDP_URL = os.environ.get('IDP_URL')
IDP_AUDIENCE = os.environ.get('IDP_AUDIENCE') or "public" 
IDP_ALG = os.environ.get('IDP_ALG') or "RS256"
