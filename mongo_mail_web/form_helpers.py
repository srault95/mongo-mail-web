# -*- coding: utf-8 -*-

from wtforms import validators
from flask_wtf.form import _is_hidden

def _is_required(field):
    for validator in field.validators:
        if isinstance(validator, (validators.DataRequired, validators.InputRequired)):
            return True
    return False
