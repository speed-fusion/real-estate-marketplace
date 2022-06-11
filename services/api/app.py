
import datetime
import pymongo

from flask_cors import CORS
from property_validations import PropertyValidations
from flask import Flask
from flask_pymongo import PyMongo

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    JWTManager,
)


from flask import request, jsonify

import logging

from bson.objectid import ObjectId

from flask_bcrypt import Bcrypt

import json

import os

username = os.environ.get("MONGO_USERNAME") 
password = os.environ.get("MONGO_PASSWORD")
host = "mongodb"
database = "real-estate"

class Database:
    def __init__(self):
        db_name = database
        connection_uri = f'mongodb://{user}:{password}@{host}/?authSource=admin'
        client = pymongo.MongoClient(connection_uri)
        db = client[db_name]
        
        self.properties = db["properties"]

db = Database()

class JSONEncoder(json.JSONEncoder):
    ''' extend json-encoder class'''

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, set):
            return list(o)
        if isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)
    


DASHBOARD_URL = ""

app = Flask(__name__,static_url_path='/static')
CORS(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "3bc27a33-ac7d-4f15-be44-2748de7c9d57"  # Change this!

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=365*10)

jwt = JWTManager(app)

flask_bcrypt = Bcrypt(app)
app.json_encoder = JSONEncoder


app.config["MONGO_URI"] = f'mongodb://{username}:{password}@{host}/{database}?authSource=admin'
mongo = PyMongo(app)

ROOT_PATH = os.getcwd()

# logger = logging.getLogger('zillow_api')
# LOG = logger.get_root_logger(__name__, filename=os.path.join(ROOT_PATH, 'output.log'))

@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({
        'ok': False,
        'msg': 'Missing Authorization Header'
    }), 401

# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jsonschema.exceptions import SchemaError

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jsonschema.exceptions import SchemaError

user_schema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
        },
        "email": {
            "type": "string",
            "format": "email"
        },
        "password": {
            "type": "string",
            "minLength": 5
        }
    },
    "required": ["email", "password"],
    "additionalProperties": False
}


preping_schema = {
    "type":"object",
    "properties":{
    "address":{
            "type":"string",
        },
    "city":{
        "type":"string",
    },
    "state":{
        "type":"string",
    },
    "zip":{
        "type":"string",
    },
    },
    "required": ["address","city","state","zip"],
    "additionalProperties": False
}


def validate_payload(data,schema):
    try:
        validate(data, schema)
    except ValidationError as e:
        return {'ok': False, 'msg': e}
    except SchemaError as e:
        return {'ok': False, 'msg': e}
    return {'ok': True, 'data': data}

property_validation = PropertyValidations()

def generate_address_query(address,city,state,zipcode):
    query = ""
    
    if address != None:
        query = query + str(address).strip() + " "
    
    if city != None:
        query = query + str(city).strip() + " "
        
    if state != None:
        query = query + str(state).strip() + " "
        
    if zipcode != None:
        query = query + str(zipcode).strip() + " "
    
    query = query.strip().lower().replace(" ","-")
    
    return query

@app.route("/pre-ping",methods=["POST"])
def preping():
    data = validate_payload(request.get_json(),preping_schema)
    if data['ok']:
        data = data['data']
        
        query = generate_address_query(data["address"],data["city"],data["state"],data["zip"])
        
        property = mongo.db.properties.find_one({"query":query})
        
        if property == None:
            return jsonify({'ok': True, 'data':{"status":False,"message":"we do not have any data for this address"}}), 200
                
        status,message = property_validation.apply_validation(property)
        
        return jsonify({'ok': True, 'data':{"status":status,"message":message[0]}}), 200
    else:
        return jsonify({'ok': False,'data':None, 'message': 'Bad request parameters: {}'.format(data['msg'])}), 400


@app.route('/auth', methods=['POST'])
def auth_user():
    ''' auth endpoint '''
    data = validate_payload(request.get_json(),user_schema)
    if data['ok']:
        data = data['data']
        user = mongo.db.users.find_one({'email': data['email']})
        
        if user and flask_bcrypt.check_password_hash(user['password'], data['password']):
            del user['password']
            del data['password']
            access_token = create_access_token(identity=data)
            refresh_token = create_refresh_token(identity=data)
            user['token'] = access_token
            user['refresh'] = refresh_token
            return jsonify({'ok': True, 'data': user}), 200
        else:
            return jsonify({'ok': False, 'msg': 'invalid username or password'}), 401
    else:
        return jsonify({'ok': False, 'msg': 'Bad request parameters: {}'.format(data['msg'])}), 400


@app.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    ''' refresh token endpoint '''
    current_user = get_jwt_identity()
    ret = {
        'token': create_access_token(identity=current_user)
    }
    return jsonify({'ok': True, 'data': ret}), 200

@app.route('/user', methods=['GET'])
@jwt_required()
def user():
    ''' route read user '''
    if request.method == 'GET':
        current_user = get_jwt_identity()
        print(current_user)
        data = mongo.db.users.find_one({"email":current_user["email"]},{"_id":0})
        del data["password"]
        return jsonify({'ok': True, 'data':data}), 200

@app.route('/register', methods=['POST'])
#@jwt_required()
def register():
    ''' register user endpoint '''
    data = validate_payload(request.get_json(),user_schema)
    if data['ok']:
        data = data["data"]
        result = mongo.db.users.find_one({"email":data["email"]})
        print(result)
        if not result:
                data['password'] = flask_bcrypt.generate_password_hash(data['password'])
                mongo.db.users.insert_one(data)
                return jsonify({'ok': True, 'msg': 'User created successfully!'}), 200
        else:
                return jsonify({'ok':False,'msg':'User already exists.'}),200
    else:
        return jsonify({'ok': False, 'msg': 'Bad request parameters: {}'.format(data['msg'])}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0")
