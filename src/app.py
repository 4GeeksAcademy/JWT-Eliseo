"""
This module takes care of starting the API Server, Loading the DB, and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_jwt_extended import JWTManager, create_access_token, jwt_required


from api.utils import APIException, generate_sitemap
from api.models import db, User
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from flask_cors import CORS

app = Flask(__name__)
app.url_map.strict_slashes = False

app.config['JWT_SECRET_KEY'] = 'chupapi'  # Replace with a strong secret key
jwt = JWTManager(app)  # Initialize JWTManager

CORS(app, origins="https://curly-barnacle-xq957grxvrvcp5j6-3000.app.github.dev")
ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"

static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

setup_admin(app)
setup_commands(app)

app.register_blueprint(api, url_prefix='/api')

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # Avoid cache memory
    return response

@app.route('/api/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    user = User.query.filter_by(email=email).first()

    if user and user.password == password:  
        
        token = create_access_token(identity=user.id)
        return jsonify({
            'token': token,
            'user': {'email': user.email}
        }), 200
    else:
        return jsonify({"msg": "Bad email or password"}), 401

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
