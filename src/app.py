"""
This module takes care of starting the API Server, Loading the DB, and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_jwt_extended import JWTManager

from api.utils import APIException, generate_sitemap
from api.models import db, User
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands

# Initialize Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'chupapi'  # Replace with a strong secret key
jwt = JWTManager(app)  # Initialize JWTManager

# Determine environment
ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"

# Static file directory configuration
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')

# Database configuration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migrations
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# Setup admin and custom commands
setup_admin(app)
setup_commands(app)

# Add all endpoints from the API with an "api" prefix
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# Any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # Avoid cache memory
    return response

# Main execution block
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
