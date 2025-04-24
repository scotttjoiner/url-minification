import os
import logging.config

from flask import Flask, Blueprint
from flask_cors import CORS
from flask_pymongo import PyMongo
from src import settings
from src.api.endpoints import ns as urls_namespace
from src.api.restplus import rest_api
#from werkzeug.middleware.proxy_fix import ProxyFix

# logging
logging.config.fileConfig( '%s/logging.conf' % os.path.dirname(os.path.abspath(__file__)))
log = logging.getLogger(__name__)

# Initialization
app = Flask(__name__)

CORS(app)

def configure_app(flask_app):
    
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP
    flask_app.config['MONGO_URI'] = settings.MONGO_URI
    flask_app.config['FLASK_DEBUG'] = settings.FLASK_DEBUG
    flask_app.config['DEBUG'] = settings.FLASK_DEBUG
    flask_app.config['FLASK_PORT'] = settings.FLASK_PORT

def initialize_app(flask_app):
    
    configure_app(flask_app)
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    rest_api.init_app(blueprint)
    rest_api.add_namespace(urls_namespace)
    flask_app.register_blueprint(blueprint)
    rest_api.mongo = PyMongo(flask_app)
    #app.wsgi_app = ProxyFix(app.wsgi_app)

def main():
    log.info('>>>>> Starting development server at http://{}/api/ <<<<<'.format(app.config['SERVER_NAME']))
    app.run(host='0.0.0.0', port=app.config['FLASK_PORT'])

# Initialization
initialize_app(app)

# Command line handler
if __name__ == "__main__":

    # Let's go!
    main()
