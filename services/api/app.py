
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

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from jsonschema.exceptions import SchemaError

from schemas import user_schema,gs_schema,preping_schema,address_schema

from GreatSchools import GreatSchools
from ZillowScraper import ZillowScraper


user = os.environ.get("MONGO_USERNAME") 
password = os.environ.get("MONGO_PASSWORD")
host = "mongodb:27017"
database = "real-estate"

class Database:
    def __init__(self):
        db_name = database
        connection_uri = f'mongodb://{user}:{password}@{host}/?authSource=admin'
        client = pymongo.MongoClient(connection_uri)
        db = client[db_name]
        
        self.properties = db["properties"]
        self.logs = db["logs"]

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


app.config["MONGO_URI"] = f'mongodb://{user}:{password}@{host}/{database}?authSource=admin'
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
    log = {}
    headers_list = request.headers.getlist("X-Forwarded-For")
    user_ip = headers_list[0] if headers_list else request.remote_addr
    log["ip_addr"] = user_ip
    log["request_body"] = request.get_json()
    log["created_at"] = datetime.datetime.now()
    if data['ok']:
        data = data['data']
        
        query = generate_address_query(data["address"],data["city"],data["state"],data["zip"])
        
        property = mongo.db.properties.find_one({"query":query,"status":"active"},{"status":0,"_id":0})
        
        if property == None:
            response_body = {"result":"Reject"}
            log["response_body"] = response_body
            log["message"] = "we don't have any data for this address"
            db.logs.insert_one(log)
            
            new_entry = {
                "query":query,
                "address":data["address"],
                "city":data["city"],
                "state":data["state"],
                "zip":data["zip"],
                "status":"pending"
            }
            
            db.properties.insert_one(new_entry)
            
            return jsonify(response_body), 200
                
        status,message = property_validation.apply_validation(property)
        
        new_status = None
        if status == False:
            new_status = "Reject"
        else:
            new_status = "Offer"
        response_body = {"result":new_status}
        log["response_body"] = response_body
        log["message"] = message
        db.logs.insert_one(log)
        return jsonify(response_body), 200
    else:
        response_body = {'ok': False,'data':None, 'message': 'Bad request parameters: {}'.format(data['msg'])}
        log["response_body"] = response_body
        db.logs.insert_one(log)
        return jsonify(response_body), 400

@app.route("/pre-ping-data",methods=["POST"])
def preping_data():
    data = validate_payload(request.get_json(),preping_schema)
    if data['ok']:
        data = data['data']
        
        query = generate_address_query(data["address"],data["city"],data["state"],data["zip"])
        
        property = mongo.db.properties.find_one({"query":query},{"status":0,"_id":0})
        
        if property == None:
            return jsonify({'ok': True, 'data':{"status":False,"message":"we do not have any data for this address","meta":None}}), 200
                
        status,message = property_validation.apply_validation(property)
        
        return jsonify({'ok': True, 'data':{"status":status,"message":message[0],"meta":property}}), 200
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


# great schools
@app.route('/greatschools',methods=['POST'])
def greatschools():
    gs = GreatSchools()
    data = validate_payload(request.get_json(),gs_schema)
    if data['ok']:
        address = data["data"]["address"]
        data = gs.fetch_data(address)
    return jsonify({'ok': True, 'data': data})
# great schools

# zillow
@app.route('/v1/zillow', methods=['POST'])
@jwt_required()
def zillow():
    data = validate_payload(request.get_json(),address_schema)
    zs = ZillowScraper()
    
    if data['ok']:
        data = data['data']
        address_str = f'{data["site_address"].strip()}-{data["site_city"].strip()}-{data["site_state"].strip()}-{data["site_zip"].strip()}'
        resp = zs.get_zillow_data(address_str)
        return jsonify({'ok':resp["status"],'msg':resp["msg"],'data':resp["data"]}),200    
    else:
        return jsonify({'ok': False, 'msg': 'Bad request parameters: {}'.format(data['msg'])}), 400


# zillow




if __name__ == "__main__":
    app.run(host="0.0.0.0")
