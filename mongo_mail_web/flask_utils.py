# -*- coding: utf-8 -*-

import datetime
import json

import arrow
from flask import current_app

def json_convert(obj):
    from bson import ObjectId
    
    if isinstance(obj, ObjectId):
        return str(obj)
    
    elif isinstance(obj, datetime.datetime):
        return arrow.get(obj).for_json()
    
    return obj

def jsonify(obj):
    content = json.dumps(obj, default=json_convert)
    return current_app.response_class(content, mimetype='application/json')
