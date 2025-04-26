# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

import os
import logging.config

from flask import Flask, Blueprint
from flask_cors import CORS
from flask_restx import Api

from src import settings
from src.api.extensions import mongo, ns as links_namespace
#from werkzeug.middleware.proxy_fix import ProxyFix

# logging
logging.config.fileConfig( '%s/logging.conf' % os.path.dirname(os.path.abspath(__file__)))
log = logging.getLogger(__name__)

def configure_app(flask_app):
    
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['RESTX_ERROR_404_HELP'] = settings.RESTX_ERROR_404_HELP
    flask_app.config['MONGO_URI'] = settings.MONGO_URI
    flask_app.config['FLASK_DEBUG'] = settings.FLASK_DEBUG
    flask_app.config['DEBUG'] = settings.FLASK_DEBUG
    flask_app.config['FLASK_RUN_PORT'] = settings.FLASK_RUN_PORT


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    configure_app(app)

    # initialize Mongo on the Flask app
    mongo.init_app(app)

    # instantiate a fresh Api *for this app*
    api = Api(
        version='1.0',
        title='URL Minification API',
        description='Operations related to URL minification',
        doc='/'  # swagger UI at /api/doc
    )

    # wire up  default error handler
    @api.errorhandler
    def default_error_handler(e):
        log.exception("An unhandled exception occurred.")
        if not app.debug:
            return {'message': 'An unhandled exception occurred.'}, 500

    # set up the API blueprint
    bp = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(bp)
    api.add_namespace(links_namespace, path='/links')
    app.register_blueprint(bp)

    return app

app = create_app()

def main():
    host = '0.0.0.0'
    port = app.config['FLASK_PORT']
    log.info(f'Starting dev server at http://{host}:{port}/api')
    app.run(host=host, port=port)

# Command line handler
if __name__ == "__main__":
    main()
