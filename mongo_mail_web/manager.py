# -*- coding: utf-8 -*-

import time
import pprint

from flask import current_app

from flask_script import Command, Option, Manager
from flask_script import prompt_bool

from werkzeug.debug import DebuggedApplication
from gevent.wsgi import WSGIServer
from flask_script.commands import Shell, Server
from decouple import config as config_from_env
    
from mongo_mail_web import constants
from mongo_mail_web import models
from mongo_mail_web import metrics

def _cmd_show_users():

    users = models.User.objects
    lines = []
    for user in users:
        roles = [r.name for r in user.roles]
        roles_str = ",".join(roles)
        active = "*" if user.active else " "
        line = u"{0:6} | {1:40} | {2:30}".format(active, user.username, roles_str)
        lines.append(line)

    print "----------------------------- USERS ----------------------------------------------------------------------"
    print u"{0:6} | {1:40} | {2:30}".format("Actif", "Username", u"Roles")
    print "----------------------------------------------------------------------------------------------------------"
    for l in lines:
        print l
    print "----------------------------------------------------------------------------------------------------------"

class ShowUsersCommand(Command):
    u"""Display user list"""
    
    def run(self, **kwargs):
        """Display user list"""
        _cmd_show_users()


def _show_config_mongoengine(app):
    #print "----------------MONGODB_SETTINGS-----------------------"
    try:
        from mongoengine.connection import _connection_settings, DEFAULT_CONNECTION_NAME
        from mongoengine import get_version as mongoengine_version
        import pymongo
        if 'MONGODB_SETTINGS' in app.config:
            print "---------------------------------"
            print "Your MONGODB_SETTINGS :"
            print "---------------------------------"        
            for key, val in app.config['MONGODB_SETTINGS'].items():
                print "%s = %s" % (key, val)
            
            print "---------------------------------"
            print "Reals Settings in mongoengine :"
            print "---------------------------------"        
            for key, val in _connection_settings.get(DEFAULT_CONNECTION_NAME).items():
                print "%s = %s" % (key, val)
                
        print "-------------------------------------------------------"
        print "Pymongo (has_c:%s).... : %s" % (pymongo.has_c(), pymongo.version)
        print "Mongoengine .......... : %s" % mongoengine_version()
        #print "-------------------------------------------------------"
                    
    except ImportError:
        print "!!! PAS DE MONGODB_SETTINGS !!!"

def _show_config(app=None):
    """
    TODO: ajout version des libs
    """
    if not app:
        app = current_app
    print "-------------------------------------------------------"
    app.config.keys().sort()
    pprint.pprint(dict(app.config))
    
    _show_config_mongoengine(app)
    
    print "-------------------------------------------------------"
    print "app.root_path          : ", app.root_path
    print "app.config.root_path   : ", app.config.root_path
    print "app.instance_path      : ", app.instance_path
    print "app.static_folder      : ", app.static_folder
    print "app.template_folder    : ", app.template_folder
    print "-------------Extensions--------------------------------"
    extensions = app.extensions.keys()
    extensions.sort()
    for e in extensions:
        print e
    print "-------------------------------------------------------"
    

def _show_urls():
    order = 'rule'
    rules = sorted(current_app.url_map.iter_rules(), key=lambda rule: getattr(rule, order))
    for rule in rules:
        methods = ",".join(list(rule.methods))
        #rule.rule = str passé au début de route()
        print "%-30s" % rule.rule, rule.endpoint, methods
    

class ShowUrlsCommand(Command):
    u"""Affiche les urls"""

    def run(self, **kwargs):
        _show_urls()

class ShowConfigCommand(Command):
    u"""Affiche la configuration actuelle de l'application"""
    
    def run(self, **kwargs):
        _show_config()        

def reset_metrics():
    models.Metric.drop_collection()
    models.MessageStore.objects.update(metric=0)
    metrics.update_metrics()
    print "metrics[%s]" % models.Metric.objects.count()

def reset_db():
    
    models.MessageStore.drop_collection()
    models.Metric.drop_collection()
    
    db = models.MessageStore._get_db()
    count = db.fs.files.remove({})
    count = db.fs.chunks.remove({})

def _create_superadmin_user(**kwargs):
    user = models.User.create_user(username=config_from_env('MMW_SUPERADMIN_EMAIL', 'admin@localhost.net'), 
                            password=config_from_env('MMW_SUPERADMIN_PASSWORD', 'password'), 
                            role='superadmin', 
                            group=constants.GROUP_DEFAULT)
    
class CreateSuperAdminCommand(Command):
    u"""Create superadmin user"""

    def run(self, **kwargs):
        _create_superadmin_user()

class ResetMetrics(Command):
    u"""Delete all metrics and recreate all"""
    
    option_list = (
                   
        Option('--quiet', 
               action="store_true", 
               dest='quiet', 
               default=False),

    )

    def run(self, quiet=False, **kwargs):
        if not quiet:
            if prompt_bool(u"Are you sure ?", default=False):
                return reset_metrics()
        else:
            return reset_metrics()

    
class ResetCommand(Command):
    u"""Delete all tables"""
    
    option_list = (
                   
        Option('--quiet', 
               action="store_true", 
               dest='quiet', 
               default=False),

    )

    def run(self, quiet=False, **kwargs):
        if not quiet:
            if prompt_bool(u"Are you sure ?", default=False):
                return reset_db()
        else:
            return reset_db()


def main(create_app_func=None):
    
    """
    TODO: commands pour créer fixtures de chaque mode pour démo
    """
    if not create_app_func:
        from mongo_mail_web.wsgi import create_app
        create_app_func = create_app
    
    class ServerWithGevent(Server):
        help = description = 'Runs the Flask development server with WSGI SocketIO Server'
    
        def __call__(self, app, host, port, use_debugger, use_reloader,
                   threaded, processes, passthrough_errors):
            #console_path='/console'
            if use_debugger:
                app = DebuggedApplication(app, evalex=True)
    
            """
            TODO: 
            from policyng_web.clients import tasks
            tasks.start_all(app)
            """
            server = WSGIServer((host, port), app)
            try:
                print 'Listening on http://%s:%s' % (host, port)
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    
    env_config = config_from_env('MMW_SETTINGS', 'mongo_mail_web.settings.Prod')
    
    manager = Manager(create_app_func, with_default_commands=False)
    manager.add_option('-c', '--config',
                       dest="config",
                       default=env_config)

    manager.add_command("shell", Shell())

    manager.add_command("server", ServerWithGevent(
                    host = '0.0.0.0',
                    port=8081)
    )

    manager.add_command("config", ShowConfigCommand())
    manager.add_command("urls", ShowUrlsCommand())
    manager.add_command("reset-db", ResetCommand())
    manager.add_command("reset-metrics", ResetMetrics())
    
    manager.add_command('users', ShowUsersCommand())
    manager.add_command('create-superadmin', CreateSuperAdminCommand())
    
    manager.run()
    

if __name__ == "__main__":
    """
    python -m mongo_mail_web.manager run -p 8081 -d -R
    
    python -m mongo_mail_web.manager -c mongo_mail_web.settings.Dev server -p 8081 -d
    
    python -m mongo_mail_web.manager urls
    
    'password' pour tous    
    """
    main()

