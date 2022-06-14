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



address_schema = {
    "type":"object",
    "properties":{
        "site_address":{
            "type":"string",
        },
        "site_city":{
            "type":"string"
        },
        "site_state":{
            "type":"string"
        },
        "site_zip":{
            "type":"string"
        },
    },
    "required": ["site_address", "site_city","site_state","site_zip"],
    "additionalProperties": False
}

gs_schema = {
    "type":"object",
    "properties":{
    "address":{
            "type":"string",
        },
    },
    "required": ["address"],
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
        "type":["string","number"],
    },
    },
    "required": ["address","city","state","zip"],
    "additionalProperties": False
}