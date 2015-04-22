# -*- coding: utf-8 -*-

import os
import uuid
import hashlib

from decouple import config
gettext = lambda s: s

from . import constants

def generate_key():
    """Génère un ID unique de 64 caractères"""
    new_uuid = str(uuid.uuid4())
    return hashlib.sha256(new_uuid).hexdigest()


class Config(object):
    
    MM_MODE = config('MMW_MODE', constants.MM_MODE_QUARANTINE, cast=int)
    
    SECRET_KEY = config('MMW_SECRET_KEY', 'azerty12345678')
    
    SENTRY_DSN = config('MMW_SENTRY_DSN', None)
    
    SESSION_ENGINE_ENABLE = config('MMW_SESSION_ENGINE_ENABLE', True, cast=bool)
    
    DEBUG = config('MMW_DEBUG', False, cast=bool)
    
    DEFAULT_THEME = config('MMW_THEME', 'slate')
    
    #---Tasks
    TASK_COMPLETED_POOL = config('MMW_TASK_COMPLETED_POOL', 10, cast=int)
    TASK_COMPLETED_SLEEP = config('MMW_TASK_COMPLETED_SLEEP', 10.0, cast=float)
    TASK_UPDATE_METRICS_SLEEP = config('MMW_TASK_UPDATE_METRICS_SLEEP', 10.0, cast=float)
    
    
    #---Flask-Babel
    TIMEZONE = "UTC"#"Europe/Paris" 
    DEFAULT_LANG = "en"
    ACCEPT_LANGUAGES = ['en', 'fr']
    
    ACCEPT_LANGUAGES_CHOICES = (
        ('en', gettext(u'English')),
        ('fr', gettext(u'French')),
    )
    
    BABEL_DEFAULT_LOCALE = DEFAULT_LANG
    BABEL_DEFAULT_TIMEZONE = TIMEZONE
    
    MONGODB_SETTINGS = {
        'db': 'message',
        'host': config('MMW_MONGODB_URI', 'mongodb://localhost:27017/message'),
        'tz_aware': True,    
    }
        
    #---Flask-Security
    SECURITY_LOGIN_USER_TEMPLATE = 'mmw/login_user.html'
    SECURITY_CHANGE_PASSWORD_TEMPLATE = "mmw/security/change_password.html"
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_PASSWORD_SALT = config('MMW_SECURITY_SALT', generate_key())
    SECURITY_URL_PREFIX = '/security'
    SECURITY_EMAIL_SENDER = 'reply@localhost'
    SECURITY_REGISTERABLE = False
    SECURITY_CONFIRMABLE = False
    SECURITY_CHANGEABLE = True
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False #Si True, envoi mail après changement de password
    SECURITY_RECOVERABLE = False #TODO: A activer pour reset pass
    SECURITY_TRACKABLE = True
    #SECURITY_UNAUTHORIZED_VIEW = "/"
    SECURITY_UNAUTHORIZED_VIEW = "/unauthorized"
    SECURITY_FLASH_MESSAGES = True
    #SECURITY_DEFAULT_HTTP_AUTH_REALM = '/'
    
    
class Prod(Config):
    pass

class Dev(Config):

    DEBUG = True

    SECRET_KEY = 'dev_key'
    
    MAIL_DEBUG = True
    
    #---debugtoolbar
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PANELS = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'flask.ext.mongoengine.panels.MongoDebugPanel',
    ]
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True

    
class Test(Config):
    
    MONGODB_SETTINGS = Config.MONGODB_SETTINGS.copy()
    MONGODB_SETTINGS['db'] = 'message_test'
    MONGODB_SETTINGS['host'] = os.environ.get('MMW_MONGODB_URI', 'mongodb://localhost:27017/message_test')

    TESTING = True    
    
    SECRET_KEY = 'test_key'
    
    WTF_CSRF_ENABLED = False
    
    PROPAGATE_EXCEPTIONS = True
    
    #CACHE_TYPE = "simple"
    CACHE_TYPE = "null"
    
    MAIL_SUPPRESS_SEND = True
    

class Custom(Config):
    pass

try:
    import local_settings
    for key in dir(local_settings):
        if not key.startswith("_") and key.isupper():
            setattr(Custom, key, getattr(local_settings, key))
except ImportError:
    pass    