# -*- coding: utf-8 -*-

from flask_moment import Moment
from flask_mongoengine import MongoEngine
from flask_security import Security

db = MongoEngine()

moment = Moment()

security = Security()

try:
    from flask_babelex import Babel, lazy_gettext, gettext, _
    babel = Babel()
    #_ = lambda s: s
    #gettext = lambda s: s
except:
    _ = lambda s: s
    gettext = lambda s: s
    class Babel(object):
        def __init__(self, *args, **kwargs):
            pass
        def init_app(self, app):
            pass
    babel = Babel()

