# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, request, abort, session, g, redirect, url_for, jsonify, render_template
from decouple import config as config_from_env

from . import PYMONGO2
from . import geoip_tools
from . import extensions
from . import admin
from . import tasks
from . import constants

THEMES = [
    #'amelia',   # ok mais pas terrible
    'cerulean', # ok
    #'cosmo',    # BAD - décallage partout
    'cyborg',  #ok
    'darkly',  #ok
    'flatly',  #ok
    'journal', # ok mais pas terrible
    'lumen',   # ok - petit mais permet ok pour colonnes
    'readable',  #ok -voir colone tableau
    'simplex', # ok - petit mais permet ok pour colonnes
    'slate',    # ok - New DEFAULT ?
    'spacelab', # ok
    'superhero', # ok mais perte visibilité dans un select
    'united',   # ok              
    #'yeti', # BAD - décallage partout
]



def _configure_themes(app):
    
    @app.before_request
    def current_theme():
        if not constants.SESSION_THEME_KEY in session:
            session[constants.SESSION_THEME_KEY] = app.config.get('DEFAULT_THEME', 'slate')
        g.theme = session.get(constants.SESSION_THEME_KEY)
            
    @app.context_processor
    def inject_theme():
        try:
            return {
                constants.SESSION_THEME_KEY: g.theme.lower(),
                'current_theme_url': url_for('static', filename='mmw/themes/bootswatch/%s/bootstrap.min.css' % g.theme.lower()),
                'themes': THEMES,                        
            }
        except AttributeError:
            return {
                constants.SESSION_THEME_KEY: app.config.get('DEFAULT_THEME', 'slate'),
                'current_theme_url': url_for('static', filename='mmw/themes/bootswatch/%s/bootstrap.min.css' % self.config('DEFAULT_THEME', 'slate')),
                'themes': THEMES,
            }

    @app.route('/change-theme', endpoint="changetheme") 
    def change_theme():
        """
        /change-theme?theme=flatly
        /fam/change-theme              fam.changetheme
        """
        new_theme = request.args.get('theme', None)
        next = request.args.get('next') or request.referrer or '/'
        #if not next:
        #    next = url_for('home')
        try:
            if new_theme:
                session[constants.SESSION_THEME_KEY] = new_theme
        except Exception, err:
            pass 
        return redirect(next)


def _configure_logging(debug=False, 
                      stdout_enable=True, 
                      syslog_enable=False,
                      prog_name='mongo_mail_web',
                      config_file=None
                      ):

    import sys
    import logging
    import logging.config
    
    if config_file:
        logging.config.fileConfig(config_file, disable_existing_loggers=True)
        return logging.getLogger(prog_name)
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'debug': {
                'format': 'line:%(lineno)d - %(asctime)s %(name)s: [%(levelname)s] - [%(process)d] - [%(module)s] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': '%(asctime)s %(name)s: [%(levelname)s] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },    
        'handlers': {
            'null': {
                'level':'ERROR',
                'class':'logging.NullHandler',
            },
            'console':{
                'level':'INFO',
                'class':'logging.StreamHandler',
                'formatter': 'simple'
            },       
        },
        'loggers': {
            '': {
                'handlers': [],
                'level': 'INFO',
                'propagate': False,
            },
            prog_name: {
                #'handlers': [],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }
    
    if sys.platform.startswith("win32"):
        LOGGING['loggers']['']['handlers'] = ['console']

    elif syslog_enable:
        LOGGING['handlers']['syslog'] = {
                'level':'INFO',
                'class':'logging.handlers.SysLogHandler',
                'address' : '/dev/log',
                'facility': 'daemon',
                'formatter': 'simple'    
        }       
        LOGGING['loggers']['']['handlers'].append('syslog')
        
    if stdout_enable:
        if not 'console' in LOGGING['loggers']['']['handlers']:
            LOGGING['loggers']['']['handlers'].append('console')

    '''if handlers is empty'''
    if not LOGGING['loggers']['']['handlers']:
        LOGGING['loggers']['']['handlers'] = ['console']
        
    if debug:
        LOGGING['loggers']['']['level'] = 'DEBUG'
        LOGGING['loggers'][prog_name]['level'] = 'DEBUG'
        for handler in LOGGING['handlers'].keys():
            LOGGING['handlers'][handler]['formatter'] = 'debug'
            LOGGING['handlers'][handler]['level'] = 'DEBUG' 

    #from pprint import pprint as pp 
    #pp(LOGGING)
    #werkzeug = logging.getLogger('werkzeug')
    #werkzeug.handlers = []
             
    logging.config.dictConfig(LOGGING)
    logger = logging.getLogger(prog_name)
    
    return logger

def _configure_security(app):
    
    from . import models
    from flask_security import MongoEngineUserDatastore
    
    datastore = MongoEngineUserDatastore(models.db, models.User, models.Role)
    state = extensions.security.init_app(app, datastore, register_blueprint=True)

def error_handlers(app):

    from flask_security import url_for_security, current_user

    @app.route('/unauthorized', endpoint="unauthorized")    
    def unauthorized_view():
        abort(403)

    @app.errorhandler(403)
    def forbidden(error):
        if not current_user.is_anonymous():
            logger.fatal("reject user [%s]" % current_user)
        logger.fatal("reject host [%s]" % request.remote_addr)
        return "forbidden. you ip address is %s" % request.remote_addr, 403

    @app.errorhandler(401)
    def unauthorized(error):
        return redirect(url_for_security('login', next=request.url))

    """    
    @app.route('/unauthorized', endpoint="unauthorized")
    def unauthorized():
        if request.args.get('json', 0, type=int) or request.is_xhr:
            return jsonify(success=False)
        return render_template("mmw/unauthorized.html")
    """

def _configure_sentry(app):
    try:
        from raven.contrib.flask import Sentry
        if app.config.get('SENTRY_DSN', None):
            sentry = Sentry(app, logging=True, level=app.logger.level)
    except ImportError:
        pass
    
def _configure_i18n(app):

    extensions.babel.init_app(app)
    babel = extensions.babel
    
    #fr <class 'babel.core.Locale'>
    #for t in babel.list_translations():
    #    print t, type(t)
    
    #current = session.get(constants.SESSION_LANG_KEY, app.config.get('DEFAULT_LANG'))
    @app.before_request
    def set_locales():
        current_lang  = session.get(constants.SESSION_LANG_KEY, None)
        if not current_lang:
            session[constants.SESSION_LANG_KEY] = app.config.get('DEFAULT_LANG')

        current_tz  = session.get(constants.SESSION_TIMEZONE_KEY, None)
        if not current_tz:
            session[constants.SESSION_TIMEZONE_KEY] = app.config.get('TIMEZONE')
    
    @babel.localeselector
    def get_locale():
        current_lang  = session.get(constants.SESSION_LANG_KEY, app.config.get('DEFAULT_LANG'))
        return current_lang
        """
        if current_user.locale:
            return current_user.locale        
        default_locale = current_app.config.get('BABEL_DEFAULT_LOCALE', 'en')
        accept_languages = current_app.config.get('ACCEPT_LANGUAGES', [default_locale])
        return request.accept_languages.best_match(accept_languages)
        """
    
    @babel.timezoneselector
    def get_timezone():
        return session.get(constants.SESSION_TIMEZONE_KEY, app.config.get('TIMEZONE'))
        
        """
        if current_user.timezone:
            return current_user.timezone
        
        return current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'UTC')
        """        

def _configure_mongolock(app):
    
    from . import metrics
    from . import models
    from mongolock import MongoLock
    metrics.lock = MongoLock(client=models.MessageStore._get_db().connection)

def _configure_processors(app):
    
    from . import constants
    from . import countries
    from . import models
    from .form_helpers import _is_hidden, _is_required

    @app.context_processor
    def form_helpers():
        return dict(is_hidden=_is_hidden, is_required=_is_required)
    
    @app.context_processor
    def langs():
        return dict(langs=app.config.get('ACCEPT_LANGUAGES_CHOICES'))

    @app.context_processor
    def current_lang():
        current = session.get(constants.SESSION_LANG_KEY, app.config.get('DEFAULT_LANG'))
        return dict(current_lang=current)

    @app.context_processor
    def current_tz():
        current = session.get(constants.SESSION_TIMEZONE_KEY, app.config.get('TIMEZONE'))
        return dict(current_tz=current)
    
    @app.context_processor
    def helpers():
        return dict(c=constants)
    
    @app.context_processor
    def country_name():
        """
        {{ country_name('fr') }}
        """
        def render(cp):
            if not cp:
                return ''
            name = countries.OFFICIAL_COUNTRIES.get(cp.upper(), '')
            return name.capitalize()
        
        return dict(country_name=render)
            
    
def create_app(config='mongo_mail_web.settings.Prod'):
    """
    TODO: before first request pour redirect vers form domains/mynetwork si aucun
    """
    
    env_config = config_from_env('MMW_SETTINGS', config)
    
    app = Flask(__name__)
    app.config.from_object(env_config)
    
    if PYMONGO2:
        app.config['MONGODB_SETTINGS']['use_greenlets'] = True
        
    app.config['LOGGER_NAME'] = 'mongo_mail_web'
    app._logger = _configure_logging(debug=app.debug, prog_name='mongo_mail_web')    
        
    extensions.db.init_app(app)
    
    _configure_mongolock(app)
    
    extensions.moment.init_app(app)
    _configure_i18n(app)
    
    _configure_security(app)
    admin.init_admin(app, url='/')
    
    _configure_processors(app)
    _configure_themes(app)
    
    geoip_tools.configure_geoip()

    if app.debug:
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)
    
    _configure_sentry(app)
    
    if app.config.get('SESSION_ENGINE_ENABLE', False):
        from flask_mongoengine import MongoEngineSessionInterface
        app.session_interface = MongoEngineSessionInterface(extensions.db)
        
    error_handlers(app)

    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    tasks.run_all_tasks(completed_pool=app.config.get('TASK_COMPLETED_POOL'),
                        completed_sleep=app.config.get('TASK_COMPLETED_SLEEP'),
                        update_metrics_sleep=app.config.get('TASK_UPDATE_METRICS_SLEEP'))
    
    return app
