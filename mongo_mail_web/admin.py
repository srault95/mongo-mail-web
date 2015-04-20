# -*- coding: utf-8 -*-

"""
REPRENDRE ICI:

TODO: setting global sur le format des date avec choix dans profil user

"""
from cStringIO import StringIO
import os
import operator
import wtforms as wtf
from jinja2 import Markup
from jinja2.filters import do_filesizeformat
from flask import abort, request, flash, redirect, url_for, render_template, g, _request_ctx_stack, session, current_app
from flask import make_response
from werkzeug.datastructures import MultiDict
from flask import send_file

from flask_security import current_user, url_for_security

from flask_admin.model.template import macro

from flask_admin import Admin, AdminIndexView as BaseAdminIndexView, expose
from flask_admin import BaseView as OriginalBaseView
from flask_admin.contrib.mongoengine.view import ModelView as BaseModelView
from flask_admin.contrib.mongoengine.view import SORTABLE_FIELDS
from flask_admin.menu import MenuLink as BaseMenuLink
from flask_admin.actions import action
from flask_admin.consts import ICON_TYPE_GLYPH
from flask_admin.contrib.mongoengine import filters
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_admin.form import FormOpts
#from flask_admin.babel import gettext, ngettext, lazy_gettext

from mongoengine import fields as mongoengine_fields
SORTABLE_FIELDS.add(mongoengine_fields.LongField)

from flask_babelex import format_date, format_datetime, format_number
import arrow
from dateutil.relativedelta import relativedelta

from . import constants
from . import models
from . import forms
from . import countries
from . import metrics
from . import metric_utils
from . import flask_utils
from . import utils
from .extensions import gettext, lazy_gettext



"""
def get_current_period():
    current_period = session.get('current_period', None)
    if not current_period:
        set_current_period()
    return session['current_period']

def set_current_period(current_period=None):
    if not current_period or not current_period in metric_utils.PERIOD_DICT.keys():
        current_period = 'last-month'    
    session['current_period'] = current_period
"""    
    
def get_current_refresh():
    current_refresh = session.get('current_refresh', None)
    if not current_refresh:
        set_current_refresh()
    return session['current_refresh']

def set_current_refresh(current_refresh=None):
    if not current_refresh:
        current_refresh = constants.REFRESH_TIME_5SEC    
    session['current_refresh'] = current_refresh
    
def size_formatter(view, context, model, name):
    return do_filesizeformat(getattr(model, name))
    
def is_in_formatter(value):

    if value == 1:
        # fa-2x
        return Markup('<i class="fa fa-arrow-left" title="%s"></i>' % gettext(u"Incoming Message"))
    elif value == 0:
        return Markup('<i class="fa fa-arrow-right" title="%s"></i>' % gettext(u"Outgoing Message"))
    else:
        return value

class IntegerBooleanEqualFilter(filters.BooleanEqualFilter):
    """
    Pour les champs is_xxx avec 0 ou 1 comme valeur
    """
    def apply(self, query, value):
        flt = {'%s' % self.column.name: value == '1'}
        return query.filter(**flt)
    
class MetricTypeEqualFilter(filters.FilterEqual):
    
    def __init__(self, column, name, options=None, data_type=None):
        filters.FilterEqual.__init__(self, column, name, options=constants.METRIC_KEY_TYPE_CHOICES, 
                                     data_type=data_type)    


class BooleanLabelFormatter(object):
    """
    BooleanLabelFormatter
    column_formatters = dict(reject_relay=BooleanLabelFormatter())
    column_formatters = dict(reject_relay=BooleanLabelFormatter(reverse=True))
    """
    
    def __init__(self, true_value=True, reverse=False, yes='label-danger', no='label-success', txt_yes=gettext(u"Yes"), txt_no=gettext(u"No")):
        self.true_value = true_value
        self.reverse = reverse
        self.yes = yes
        self.no = no 
        self.txt_yes = txt_yes
        self.txt_no = txt_no
        
    def __call__(self, view, context, model, name):
        
        if not self.reverse:
            label_yes = '<span class="label %s">%s</span>' % (self.yes, self.txt_yes)
            label_no = '<span class="label %s">%s</span>' % (self.no, self.txt_no)
        else:
            label_yes = '<span class="label %s">%s</span>' % (self.no, self.txt_no)
            label_no = '<span class="label %s">%s</span>' % (self.yes, self.txt_yes)
        
        value = getattr(model, name, None)
        if value == self.true_value:
            return Markup(label_yes)
        else:
            return Markup(label_no)
        
def filter_formatter(view, context, model, name):
    value = model.filter_result
    color = "label-default"
    if value == "CLEAN":
        color = "label-success"
    elif value == "SPAM":
        color = "label-warning"
    elif value == "VIRUS":
        color = "label-danger"
    elif value == "BANNED":
        color = "label-info"
    elif value == "UNCHECKED":
        color = "label-danger"
    return Markup('<span class="label %s">%s</span>' % (color, value))

def queue_formatter(view, context, model, name):

    queue = model.queue
    #queue_display = model.get_queue_display()
    
    queue_map = {
        constants.MESSAGE_QUEUE_INCOMING: '<button class="btn btn-primary btn-block disabled"><i class="fa fa-download"></i> Incoming</button>',
        constants.MESSAGE_QUEUE_ACTIVE: '<button class="btn btn-success btn-block disabled"><i class="fa fa-refresh"></i> Active</button>',
        constants.MESSAGE_QUEUE_DEFERRED: '<button class="btn btn-warning btn-block disabled"><i class="fa fa-lock"></i> Deferred</button>',
        constants.MESSAGE_QUEUE_DELIVERY: '<button class="btn btn-info btn-block disabled"><i class="fa fa-share"></i> Delivery</button>',
        constants.MESSAGE_QUEUE_QUARANTINE: '<button class="btn btn-warning btn-block disabled"><i class="fa fa-anchor"></i> Quarantine</button>',
        constants.MESSAGE_QUEUE_TURING: '<button class="btn btn-warning btn-block disabled"><i class="fa fa-user"></i> Turing</button>',
        constants.MESSAGE_QUEUE_HOLD: '<button class="btn btn-warning btn-block disabled"><i class="fa fa-lock"></i> Hold</button>',
        constants.MESSAGE_QUEUE_DELETED: '<button class="btn btn-info btn-block disabled"><i class="fa fa-trash-o"></i> Delete</button>',
        constants.MESSAGE_QUEUE_ARCHIVED: '<button class="btn btn-info btn-block disabled"><i class="fa fa-suitcase"></i> Archived</button>',
        constants.MESSAGE_QUEUE_ERROR: '<button class="btn btn-danger btn-block disabled"><i class="fa fa-lock"></i> Error</button>',
    }
    
    return Markup(queue_map[queue])        

class LimitValueFormatter(object):
    
    def __init__(self, max_value=20):
        self.max_value = max_value 
        
    def __call__(self, view, context, model, name):

        value = getattr(model, name, None)
        if not value:
            return value
        
        if value and len(value) > self.max_value:
            return Markup('<span title="%s">%s...</span>' % (value, value[:self.max_value]))
        return value

value_limiter = LimitValueFormatter(25)

def local_limiter(value, max_value=25):
    if value and len(value) > max_value:
        return Markup('<span title="%s">%s...</span>' % (value, value[:max_value]))
        #return "%s..." % value[:max_value]
    return value

def formatter_country_name(country):
    u"""Return country name"""
    if not country:
        return ""
    return countries.OFFICIAL_COUNTRIES.get(country.upper(), '').capitalize()

def rcpt_formatter(view, context, model, name):
    rcpt = model.rcpt
    if len(rcpt) == 0:
        return ""
    elif len(rcpt) == 1:
        return local_limiter(rcpt[0])
    
    rcpts = []
    for r in rcpt:
        rcpts.append("<li>%s</li>" % r)
    
    html = """
    <a href="#" data-row-target="#rcpt_%(id)s" class="rcpt_more">
        <i class="glyphicon glyphicon-plus"></i>
    </a>
    <div id="rcpt_%(id)s" style="display: none;">
    <ul>
        %(rcpts)s
    </ul>
    </div>
    """ % dict(id=model.id, rcpts="".join(rcpts))
    
    return Markup(html)

class RoledView(object):

    def is_visible(self):
        if not current_user.is_authenticated():
            return False
        return True

    def is_accessible(self):
        if current_user.is_anonymous():
            return False
        
        return True
    
    def inaccessible_callback(self, name, **kwargs):
        """
        Call if is_accessible return False
        
        If user is not authenticated, return 401, unauthorized for redirect login view
        
        If user is authenticated, return 403, forbiden error
        """
        if not current_user.is_authenticated():
            return abort(401)
        
        return abort(403)

class BaseView(RoledView, OriginalBaseView):
    pass
    
class AuthenticatedMenuLink(BaseMenuLink):
    
    def is_accessible(self):
        return current_user.is_authenticated()
        

class AccountMenu(BaseView):
    u""" MenuView utilisateur
    
    /change                        security.change_password HEAD,POST,OPTIONS,GET
    /login                         security.login HEAD,POST,OPTIONS,GET
    /logout                        security.logout HEAD,OPTIONS,GET
    /reset                         security.forgot_password HEAD,POST,OPTIONS,GET
    /reset/<token>                 security.reset_password HEAD,POST,OPTIONS,GET
    
    /admin/user_menu/              user_menu.index HEAD,OPTIONS,GET
    /admin/user_menu/change-password user_menu.profile HEAD,POST,OPTIONS,GET
    /admin/user_menu/logout        user_menu.logout HEAD,OPTIONS,GET            
    """

    def is_visible(self):
        return False
    
    @expose('/')
    def index(self):
        return redirect('/')

    @expose('/change-password', methods=('GET', 'POST'))
    def change_password(self):
        """
        SECURITY_CHANGE_URL: /change
        
        SECURITY_POST_RESET_VIEW: None :  view to redirect to after a user successfully resets their password.
        SECURITY_POST_CHANGE_VIEW: edirect to after a user successfully changes their password
        
        
        
        security.change_password
        """
        from flask_security import views
        from flask_security.forms import ChangePasswordForm
        
        #user = models.User.objects.get(id=current_user.get_id())
        user = current_user._get_current_object()
        form = forms.ChangePasswordForm(request.form, obj=user)
         
        if form.validate_on_submit():
            #locale = user.locale
            #timezone = user.timezone
            form.populate_obj(user)
            user.save()
            refresh()
            flash(gettext(u"Your profile has been saved"))
            return redirect(url_for('.profile'))
        else:
            if request.method in ("PUT", "POST"):
                flash(gettext(u"form did not validate on submit"))
            #elif request.method == 'GET':
            #    form['locale'].choices = current_app.config.get('ACCEPT_LANGUAGES_CHOICES')
                
        return self.render('fam/admin/user_profile.html', form=form, data=user)

    @expose('/change-lang', methods=('GET',))
    def change_lang(self):
        """
        {{ url_for('user_menu.change_lang') }}?locale=fr
        """
        
        from flask_babelex import refresh
        locale = request.args.get("locale", None)
        current_lang  = session.get(constants.SESSION_LANG_KEY, None)

        if locale and current_lang and locale != current_lang and locale in current_app.config.get('ACCEPT_LANGUAGES'):
            session[constants.SESSION_LANG_KEY] = locale
            refresh()
        
        next = request.args.get("next") or request.referrer or request.url
        return redirect(next)
        
        #return flask_utils.jsonify(dict(success=True))
    
    
    @expose('/logout', methods=('GET',))
    def logout(self):
        return redirect(url_for_security('logout'))     

    @expose('/change-password', methods=('GET', 'POST'))
    def change_password(self):
        return redirect(url_for_security('change_password'))     


class ModelView(RoledView, BaseModelView):

    #form_base_class = BaseForm
    action_disallowed_list = ['untrash', 'trash'] #'delete', 
    
    """
    TODO: Idée: utiliser un champs qui contient les hiddens pour alimenter automatiquement form_overrides
    """
    form_overrides = dict(internal_field=wtf.HiddenField,
                          mark_for_delete=wtf.HiddenField)
    
    def __init__(self, model, roles_access=None, **kwargs):
        self.roles_access = roles_access
        BaseModelView.__init__(self, model, **kwargs)
        
    #FIXME: count !
    @action('trash',
            lazy_gettext(u'Push to trash'),
            lazy_gettext(u'Are you sure ?'))
    def action_trash(self, ids):
        qs = self.model.objects(id__in=ids)
        count = qs.update(set__mark_for_delete=1, multi=True)
        if count:
            flash(gettext(u"%(count)s records has been push to trash.", count=count))

    #FIXME: count !
    @action('untrash',
            lazy_gettext(u'Restore from trash'),
            lazy_gettext(u'Are you sure ?'))
    def action_untrash(self, ids):
        qs = self.model.objects(id__in=ids)
        count = qs.update(set__mark_for_delete=0, multi=True)
        if count:
            flash(gettext(u"%(count)s records has been restore from trash.", count=count))

    show_template = 'mmw/admin/model/show.html'
    
    list_template = 'mmw/admin/model/list.html'
    
    columns_style = {}
    
    columns_show_link = None

    #TODO: page_size
    """        
    DEFAULT_PAGE_SIZE = 10
    def get_page_size(self):        
        if current_user.is_authenticated():
            return current_user.per_page
        return self.DEFAULT_PAGE_SIZE
    page_size = property(fget=get_page_size)
    """
    page_size = 10
    
    def get_column_title_field(self, name):
        return self.column_descriptions.get(name, gettext('Sort by %(name)s', name=name))
    
    def get_column_style(self, name):
        if name in self.columns_style:
            return Markup('style="%s"' % self.columns_style.get(name))
        return ""

    @expose('/')
    def index_view(self):
        self._template_args['get_column_style'] = self.get_column_style
        self._template_args['columns_show_link'] = self.columns_show_link
        self._template_args['get_column_title_field'] = self.get_column_title_field
        return BaseModelView.index_view(self)
    
    @expose('/delete/', methods=('POST',))
    def delete_view(self):
        if current_app.config.get('DEMO_MODE', False):
            return_url = self.get_url('.index_view')
            flash(gettext('Not available function in Demo Mode.'))
            return redirect(return_url)
            
        return BaseModelView.delete_view(self)
        
    @expose('/show/', methods=('GET',))
    def show_view(self):

        return_url = get_redirect_target() or self.get_url('.index_view')

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            return redirect(return_url)

        form = self.edit_form(obj=model)

        self.on_form_prefill(form, id)

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_edit_rules)

        return self.render(self.show_template,
                           model=model,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)
        
    def get_column_descriptions(self):
        u"""Utilise le help_text du champs quand il existe
        
        Appellé par le template model/list.html et view._refresh_cache(self)
        
        Renvoi un texte de description de la colonne qui sera affiché par un icon
        à coté du libellé de colonne.
        
        Syntaxe normale:
            column_descriptions = dict(
                name='First and Last name'
            )
        
        """
        
        #Demande liste de colonne qui seront affichés
        columns = self.get_list_columns()
        descriptions = dict()
        for name, display in columns:
            #Demander le champs du model
            _model_field = getattr(self.model, name, None)
            value = getattr(_model_field, 'help_text', None)
            if value:
                descriptions[name] = getattr(_model_field, 'help_text')
                
        if self.column_descriptions:
            descriptions.update(self.column_descriptions)
            
        return descriptions

    def get_column_name(self, field):
        u""" Permet d'utiliser le verbose_name des champs pour le libellé de colonne
        
        Attention, intercepte l'utilisation de self.column_labels
        
        Méthode appellé par 
            get_list_columns()
                return [(c, self.get_column_name(c)) for c in columns]
        """
        if self.column_labels and field in self.column_labels:
            return BaseModelView.get_column_name(self, field)
        
        #TODO: si embeded, il faut aller chercher les champs
        
        _model_field = getattr(self.model, field, None)
        if hasattr(_model_field, 'verbose_name'):

            #Seulement si not None
            if getattr(_model_field, 'verbose_name'):
                return getattr(_model_field, 'verbose_name')

        #Renvoi le nom du champs par défault en capitalize
        #renvoi un str        
        return BaseModelView.get_column_name(self, field)
    
    def _refresh_cache(self):
        u"""Surcharge pour mettre à jour self.column_descriptions 
        """
        self.column_descriptions = self.get_column_descriptions()
        BaseModelView._refresh_cache(self)
        
    def get_query(self):
        return self.model.objects(mark_for_delete__ne=1)

class AdminIndexView(RoledView, BaseAdminIndexView):
    
    @expose()
    def index(self):
        """
        TODO: current period ! : use g.xxx ?
        """
        
        #self._template_args['refresh_choices'] = constants.REFRESH_CHOICES
        #self._template_args['refresh_choices_dict'] = dict(constants.REFRESH_CHOICES)
        
        """
        top_country_current_field = request.args.get('top_country_current_field', getattr(g, 'top_country_current_field', 'mail_count'))
        if not top_country_current_field in MetricView.valid_fields:
            top_country_current_field = 'mail_count'
        g.top_country_current_field = top_country_current_field
        self._template_args['top_country_current_field'] = top_country_current_field
        """

        last_refresh = get_current_refresh()
        current_refresh = request.args.get('current_refresh', last_refresh, type=int)
        if current_refresh != last_refresh:
            set_current_refresh(current_refresh)        
        self._template_args['current_refresh'] = current_refresh

        return BaseAdminIndexView.index(self)


class RoleModelView(ModelView):
    
    column_list = ('name', 'active')
    

class UserModelView(ModelView):
    
    column_list = ('email', 'active', 'last_login_at', 'login_count')
    

class MongoSystem(BaseView):
    
    @expose('/', methods=('GET',))
    def index(self):
        db = models.MessageStore._get_db()
        conn = db.connection
        collname = models.MessageStore._get_collection_name()
        coll = db[collname]

        ctx = {
            'object_list': models.MessageStore.objects,
            'dbstats': db.command({'dbstats': 1}),
            'collection_names': db.collection_names(),
            'collstats': db.command({'collstats': collname}),
            'collindex': coll.index_information(),
            'colloptions': coll.options(),
            'count': models.MessageStore.objects.count(),
            #conn['admin'].command({"buildinfo": 1})
        }
        return self.render('mmw/mongodb/debug.html', **ctx)
    
class DomainView(ModelView):

    column_list = ('name',)
    
    column_editable_list = ('name', )

    #can_delete = False    
    #can_create = False
    #can_edit = False
    
    @expose('/import', methods=('POST', 'GET'))
    def import_domains(self):
        """
        DomainImportForm
        """
        form = forms.DomainImportForm()
        errors = []
        if form.validate_on_submit():
            domains = form.data.get('domains', "").split(os.linesep)
            for domain in domains:
                try:
                    if domain and domain.strip():
                        models.Domain(name=domain).save()
                except Exception, err:
                    errors.append(str(err))
            if len(errors) == 0:
                return redirect(url_for(".index_view"))                            
        
        return self.render('mmw/admin/model/import-domains.html', 
                           form=form, errors=errors, 
                           return_url=url_for(".index_view"))
        
    
class DomainViewTrash(DomainView):
        
    action_disallowed_list = ['trash']    

    can_create = False
    can_edit = False

    #def is_visible(self):
    #    return False
        
    def get_query(self):
        return self.model.objects(mark_for_delete__ne=0)
    
    
class MynetworkView(ModelView):
    
    column_list = ('ip_address', 'comments')
    
class TransportView(ModelView):

    column_list = ('address', 'comments')
    
    column_editable_list = ('address', 'comments')


class MetricModelView(ModelView):
    
    list_template = "mmw/admin/model/metric/list.html"
    
    action_disallowed_list = ['delete', 'untrash', 'trash']
    
    can_edit = False
    can_create = False
    can_delete = False

    #TODO: call moment() from column_formatters
    column_formatters = {
        "date": lambda v, c, m, n: format_datetime(m.date, format='short'),
        "key_type": lambda v, c, m, n: m.get_key_type_display(),
        "metrics.total_size": lambda v, c, m, n: do_filesizeformat(m.metrics.total_size),
    }
    
    column_list = ['group_name', 'date', 'key', 'key_type', 
                   'metrics.count', 'metrics.mail_in', 'metrics.mail_out', 
                   'metrics.clean', 'metrics.spam', 'metrics.virus', 'metrics.banned', 'metrics.unchecked',
                   'metrics.bounce',
                   'metrics.files_count',  
                   'metrics.total_size']
    
    column_filters = ['group_name', 'date', 'key',
                      MetricTypeEqualFilter(models.Metric.key_type, "Key Type")]

    column_labels = {
        'metrics.count': gettext(u"All"),
        'metrics.mail_in': gettext(u"Incoming"),
        'metrics.mail_out': gettext(u"Outgoing"),
        'metrics.clean': gettext(u"Clean"),
        'metrics.spam': gettext(u"Spam"),
        'metrics.virus': gettext(u"Infected"),
        'metrics.banned': gettext(u"Banned"),
        'metrics.unchecked': gettext(u"Unchecked"),
        'metrics.bounce': gettext(u"Bounce"),
        'metrics.files_count': gettext(u"Files"),
        'metrics.total_size': gettext(u"Size"),
    } 
    
    def get_query(self):
        return self.model.objects

class MetricModelGroupView(MetricModelView):
    
    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]

    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_GROUP)

class MetricModelIPView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_IP)
    
class MetricModelCountryView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_COUNTRY)


class MetricModelServerView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_SERVER)

class MetricModelDomainRefView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_DOMAIN_REF)

class MetricModelDomainView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_DOMAIN)

class MetricModelDomainSenderView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_DOMAIN_SENDER)

class MetricModelDomainRecipientView(MetricModelView):

    column_list = [l for l in MetricModelView.column_list if not l in ['key_type']]
    
    column_filters = ['group_name', 'date', 'key']

    def get_query(self):
        return self.model.objects(key_type=constants.METRIC_KEY_TYPE_DOMAIN_RECIPIENT)

class MetricView(BaseView):
    
    valid_fields = ['mail_count', 'mail_in', 'mail_out', 
                    'size_sum', 'size_avg', 
                    'clean', 'spam', 'virus', 'banned', 'unchecked',
                    'bounce', 'files_count']
    
    fields_choices = [
        ("mail_count", gettext(u"By Count")),
        #("mail_in", gettext(u"By Number - Messages Incoming")),
        #("mail_out", gettext(u"By Number - Messages Outgoing")),
        ("size_sum", gettext(u"By Size")),
        ("size_avg", gettext(u"By Average Size")),
        ("clean", gettext(u"By Clean")),
        ("spam", gettext(u"By Spam")),
        ("virus", gettext(u"By Infected")),
        ("banned", gettext(u"By Banned")),
        ("unchecked", gettext(u"By Unchecked")),
        ("bounce", gettext(u"By Bounced")),
    ]
    
    field_subtitles = {
        'mail_count': gettext(u"All Messages - By Count"),
        'mail_in': gettext(u"Incoming - By Count"),
        'mail_out': gettext(u"Outgoing - By Count"),
        'size_sum': gettext(u"All Messages - By Sum size"),
        'size_avg': gettext(u"All Messages - By Average size"),
        'spam': gettext(u"All Messages - By Spam count"),
        'virus': gettext(u"All Messages - By Virus count"),
        'banned': gettext(u"All Messages - By Banned count"),
        'unchecked': gettext(u"All Messages - By Unchecked count"),
        'bounce': gettext(u"All Messages - By Bounce count"),
        'files_count': gettext(u"All Messages - By Files count"),
    }
    
    def is_visible(self):
        return False
    
    def _previous_period(self, first, last):
        seconds = last - first
        new_first = first - seconds
        new_last = last - seconds
        return dict(first_time=new_first, last_time=new_last)
    
    def _parse_period(self, _period=None):
        """
        > Première entrée de cette période
        arrow.utcnow().floor('hour')
        <Arrow [2013-05-07T05:00:00+00:00]>
        
        > Dernière entrée de cette période
        arrow.utcnow().ceil('hour')
        <Arrow [2013-05-07T05:59:59.999999+00:00]>
        
        arrow.utcnow().ceil('hour') - arrow.utcnow().floor('hour')
        datetime.timedelta(0, 3599, 999999)        

        d = arrow.utcnow().ceil('hour') - arrow.utcnow().floor('hour')
        d.total_seconds()
        3599.999999        
        
        > Maintenant - 1 AN - Attention, years et pas year
        arrow.utcnow().replace(years=-1)
        <Arrow [2014-04-17T22:15:55.488000+00:00]>
        
        len(arrow.Arrow.span_range('hour', first, last))
        8761        
        
        arrow.Arrow.span_range('month', first, last)
        last = arrow.utcnow()
        first = last.replace(years=-1)
        > 2 entrée par mois situé entre first et last (chaque début et fin de mois)
        arrow.Arrow.span_range('month', first, last)
        > 2 entrée par jour (366 entrées)
        arrow.Arrow.span_range('day', first, last)
        
        
        > Lendemain à zéro: NOK
        arrow.utcnow().ceil('day').replace(second=1)
        <Arrow [2015-04-15T23:59:59.000001+00:00]>
        
        arrow.utcnow().span('day')
        (<Arrow [2015-04-15T00:00:00+00:00]>,
        <Arrow [2015-04-15T23:59:59.999999+00:00]>)
        
        > 1 entrée (start/end) par heure pour la date en cours
        arrow.Arrow.span_range('hour', *arrow.utcnow().span('day'))
        
        > pour avoir un tableau de début, fin par jour sur le mois en cours du 1 au 30 ou 31
        arrow.Arrow.span_range('day', *arrow.utcnow().span('month'))
        [(<Arrow [2015-04-01T00:00:00+00:00]>,
          <Arrow [2015-04-01T23:59:59.999999+00:00]>),
         (<Arrow [2015-04-02T00:00:00+00:00]>,
          <Arrow [2015-04-02T23:59:59.999999+00:00]>),
         (<Arrow [2015-04-03T00:00:00+00:00]>,
          <Arrow [2015-04-03T23:59:59.999999+00:00]>),
         (<Arrow [2015-04-04T00:00:00+00:00]>,
          <Arrow [2015-04-04T23:59:59.999999+00:00]>),        
        """
        #_period = _period or get_current_period()
        if not _period in metric_utils.PERIOD_DICT:
            _period = 'last-month'
        
        if _period == "today":
            today = arrow.utcnow().span('day')
            return dict(first_time=today[0].datetime, last_time=today[1].datetime)
            
        period = metric_utils.PERIOD_DICT.get(_period)
        p = metric_utils.period_request(period, default_timezone='UTC')
        return dict(first_time=p['startTime'], last_time=p['endTime'])

    @expose('/')
    def index(self):
        return redirect(url_for('.group_by_period'))

    @expose('/by-period/label/', methods=('GET',))
    def group_by_period_label(self):
        """
        - Alimentation des label
        """
        current_period = request.args.get('period', 'last-month')
        if not current_period in metric_utils.PERIOD_DICT:
            current_period = 'last-month'
        
        period_kwargs = self._parse_period(current_period)
        qs = models.Metric.objects(key_type=constants.METRIC_KEY_TYPE_GROUP,
                           date__gte=period_kwargs['first_time'],
                           date__lt=period_kwargs['last_time'])

        current_stats = {
            'mail_count': qs.sum('metrics.count'), #TODO: clone ?
            'mail_in': qs.sum('metrics.mail_in'),
            'mail_out': qs.sum('metrics.mail_out'),
            'clean': qs.sum('metrics.clean'),
            'spam': qs.sum('metrics.spam'),
            'virus': qs.sum('metrics.virus'),
            'banned': qs.sum('metrics.banned'),
            'bounce': qs.sum('metrics.bounce'),
            #'unchecked': qs.sum('metrics.unchecked'),
            'total_size': qs.sum('metrics.total_size'),
            #'total_size': do_filesizeformat(qs.sum('metrics.total_size')),
        }

        previous_period = self._previous_period(period_kwargs['first_time'], period_kwargs['last_time'])
        previous_qs = models.Metric.objects(key_type=constants.METRIC_KEY_TYPE_GROUP,
                           date__gte=previous_period['first_time'],
                           date__lt=previous_period['last_time'])
        
        previous_stats = {
            'mail_count': previous_qs.sum('metrics.count'),
            'mail_in': previous_qs.sum('metrics.mail_in'),
            'mail_out': previous_qs.sum('metrics.mail_out'),
            'clean': previous_qs.sum('metrics.clean'),
            'spam': previous_qs.sum('metrics.spam'),
            'virus': previous_qs.sum('metrics.virus'),
            'banned': previous_qs.sum('metrics.banned'),
            'bounce': previous_qs.sum('metrics.bounce'),
            #'unchecked': previous_qs.sum('metrics.unchecked'),
            #'total_size': do_filesizeformat(previous_qs.sum('metrics.total_size')),
            'total_size': previous_qs.sum('metrics.total_size'),
        }
        
        diff_stats = {
            'mail_count': 0,
            'mail_in': 0,
            'mail_out': 0,
            'clean': 0,
            'spam': 0,
            'virus': 0,
            'banned': 0,
            'bounce': 0,
            #'unchecked': previous_qs.sum('metrics.unchecked'),
            'total_size': 0,
        }
        for k in diff_stats.keys():
            diff_stats[k] = utils.percent_calcul(current_stats, previous_stats, k)
        
        kwargs = dict(data=current_stats, 
                      previous_data=previous_stats,
                      diff_data=diff_stats,
                      current_period=current_period)
        kwargs.update(period_kwargs)
        kwargs['previous_period'] = previous_period
        
        return flask_utils.jsonify(kwargs)

    @expose('/group-by-period/', methods=('GET',))
    def group_by_period(self):
        """
        Used by metric_per_period
        
        TODO: Si period today ou yesterday ou last-24, renvoyé un tableau par heure ?
        
        TODO: modifier les args pour faire comme graphite: from: '-24hours', until: 'now',
        """        
        #is_html = request.args.get('html', 0, type=int)
        #standalone = request.args.get('standalone', 0, type=int)
        #current_step = request.args.get('step', 'ymd')
        current_step = 'ymdh'

        current_period = request.args.get('period', 'last-month')
        if not current_period in metric_utils.PERIOD_DICT:
            current_period = 'last-month'
        period_kwargs = self._parse_period(current_period)
        
        #if current_period in ['today', 'yesterday', 'last-24-hours']:
        #    period_kwargs['date_hour'] = True
        if current_step == 'y':
            #period_kwargs['date_month'] = True
            period_kwargs['date_day'] = False
        elif current_step == 'ym':
            period_kwargs['date_day'] = True
        elif current_step == 'ymdh':
            period_kwargs['date_hour'] = True
        #elif current_step == 'ymdhmn':
        #    period_kwargs['date_hour'] = True
        #    period_kwargs['date_minute'] = True
            
        result = metrics.metrics_query(key_type=constants.METRIC_KEY_TYPE_GROUP,
                                       sort_desc=False,
                                       is_group_key=False, 
                                       **period_kwargs)
        
        stats = []
        for r in result:
            _date = arrow.get(metrics.to_utc_datetime(**r.pop('_id'))).timestamp * 1000
            r['date'] = _date
            stats.append(r)
            
        kwargs = dict(data=stats, 
                      current_period=current_period, 
                      current_step=current_step,
                      first_time_timestamp=arrow.get(period_kwargs['first_time']).timestamp * 1000,
                      last_time_timestamp=arrow.get(period_kwargs['last_time']).timestamp * 1000,
                      json_first_time=arrow.get(period_kwargs['first_time']).for_json(),
                      json_last_time=arrow.get(period_kwargs['last_time']).for_json(),                      
                      )
        kwargs.update(period_kwargs)

        """        
        if is_html:
            return self.render('mmw/metrics/group-by-day.html',
                               standalone=standalone==1,
                               current_period=current_period, 
                               **kwargs)
        """                            
        
        return flask_utils.jsonify(kwargs)
        
    @expose('/top/multi-generic/', methods=('GET',))
    def top_multi_generic(self):
        
        key_type = request.args.get('key_type', constants.METRIC_KEY_TYPE_GROUP, type=int)
        limit = request.args.get('limit', 10, type=int)
        is_html = request.args.get('html', 0, type=int)
        
        current_period = request.args.get('period', 'last-month')
        if not current_period in metric_utils.PERIOD_DICT:
            current_period = 'last-month'
        period_kwargs = self._parse_period(current_period)

        url = "%s?html=%s&limit=%s&key_type=%s&period=%s" % (url_for('.top_multi_generic'), is_html, limit, key_type, current_period)
        
        result = metrics.metrics_query(key_type=key_type,
                                       date_month=False, date_day=False, date_year=False,
                                       **period_kwargs)

        top_metrics = {}
        
        for field in self.valid_fields:
            top_metrics[field] = metrics.metrics_top_convert(result, limit=limit, field=field)
            
        kwargs = dict(metrics=top_metrics,
                      url=url, 
                      limit=limit,
                      key_type=key_type,
                      type_kb=False,
                      current_period=current_period,
                      json_first_time=arrow.get(period_kwargs['first_time']).for_json(),
                      json_last_time=arrow.get(period_kwargs['last_time']).for_json(),
                      )
         
        kwargs.update(period_kwargs)
        if field in ['size_sum', 'size_avg']:
            kwargs['type_kb'] = True
            
        if is_html:
            return self.render('mmw/metrics/multi-top-generic.html',
                               #fields_choices=self.fields_choices,
                               **kwargs)
        
        return flask_utils.jsonify(kwargs)
        

    @expose('/top/by-country/', methods=('GET',))
    def top_country_count(self):
        
        field = request.args.get('field', 'mail_count')
        is_html = request.args.get('html', 0, type=int)

        current_period = request.args.get('period', 'last-month')
        if not current_period in metric_utils.PERIOD_DICT:
            current_period = 'last-month'
        period_kwargs = self._parse_period(current_period)
        
        result = metrics.metrics_top_country(limit=10, field=field, 
                                                     **period_kwargs)
        
        kwargs = dict(metrics=result, 
                      field=field, 
                      type_kb=False,
                      current_period=current_period,
                      json_first_time=arrow.get(period_kwargs['first_time']).for_json(),
                      json_last_time=arrow.get(period_kwargs['last_time']).for_json(),
                      title=gettext(u"By Country"),
                      subtitle=self.field_subtitles[field]) #"%s Country" %
         
        kwargs.update(period_kwargs)
        if field in ['size_sum', 'size_avg']:
            kwargs['type_kb'] = True
        
        if is_html:
            return self.render('mmw/metrics/top_country.html',
                               fields_choices=self.fields_choices,
                               **kwargs)
        
        return flask_utils.jsonify(kwargs)
        

class MessageStoreBaseView(ModelView):
    
    list_template = "mmw/admin/model/message_store/list.html"
    show_template = 'mmw/admin/model/message_store/show.html'
    
    column_labels = dict(is_in=gettext(u"Way"),
                         rcpt_count=gettext(u'Rcpts'),
                         filter_result=gettext(u"Filter")) 

    #columns_style = {'received': 'width: 120px;'}
    
    columns_show_link = 'sender'
        
    can_edit = False
    can_create = False
    can_delete = False    
    
    action_disallowed_list = ModelView.action_disallowed_list + ['delete']
    
    column_list = ['sender',
                   'received', 
                   'rcpt', 
                   'rcpt_count',
                   'is_in',
                   'client_address', 
                   'country', 
                   'size', 
                   'files_count', 
                   #'is_spam', 'is_virus', 'is_banned', 'is_unchecked',
                   'filter_result', 
                   'is_bounce']
    
    column_filters = ('group_name', 'received', 'sender', 'client_address', 'size',
                      IntegerBooleanEqualFilter(models.MessageStore.is_in, 'Incoming'),
                      IntegerBooleanEqualFilter(models.MessageStore.is_spam, 'Spam'),
                      IntegerBooleanEqualFilter(models.MessageStore.is_virus, 'Virus'),
                      IntegerBooleanEqualFilter(models.MessageStore.is_banned, 'Banned'),
                      IntegerBooleanEqualFilter(models.MessageStore.is_unchecked, u'Unchecked'),
                      filters.FilterLike(models.MessageStore.rcpt, gettext(u'Recipients')),
                      filters.FilterInList(models.MessageStore.rcpt, gettext(u'Recipients')))
    
    column_searchable_list = ['sender', 'client_address']

    column_formatters = dict(is_in=lambda v, c, m, n: is_in_formatter(m.is_in),
                             queue=queue_formatter,
                             size=size_formatter,
                             rcpt=rcpt_formatter,
                             country=lambda v, c, m, n: formatter_country_name(m.country),
                             sender=value_limiter,
                             sent=lambda v, c, m, n: format_datetime(m.sent, format='short'),
                             received=lambda v, c, m, n: format_datetime(m.received, format='short'),
                             filter_result=filter_formatter,
                             is_spam=BooleanLabelFormatter(true_value=1),
                             is_virus=BooleanLabelFormatter(true_value=1),
                             is_banned=BooleanLabelFormatter(true_value=1),
                             is_unchecked=BooleanLabelFormatter(true_value=0, no='label-danger', yes='label-success'),
                             is_bounce=BooleanLabelFormatter(true_value=1),
                             )

    @expose('/download/', methods=('GET', ))
    def download_view(self):
        id = request.args.get('id')
        
        message = models.MessageStore.objects(id=id).first()
        if not message:
            abort(400, "object not found")
        
        #TODO: ajout lien download dans show.html 
        #TODO: dialog pour choix options
        #TODO: header only
        #TODO: option compress
        #TODO: format eml
        #TODO: recevoir par mail
         
        message_str = message.parse_message(pure_string=True)
        io = StringIO(message_str)
        io.seek(0)
        return send_file(io,
                         #io.BytesIO(message_str),                          
                         mimetype='text/plain', 
                         as_attachment=True, 
                         attachment_filename='%s.txt' % message.store_key)
        
        """
        response = make_response(message_str)
        #res.content_type = 'text/plain'
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = 'attachment; filename=%s.txt' % message.store_key        
        return res
        """        
    
    @expose('/show/', methods=('GET', ))
    def show_view(self):
        id = request.args.get('id')
        
        message = models.MessageStore.objects(id=id).first()
        if not message:
            abort(400, "object not found")
            
        self._template_args['email'] = message.parse_message()
        
        return ModelView.show_view(self)

    #@action('reparse',
    #        lazy_gettext(u'Reload analysis'),
    #        )
    def action_reparse(self, ids):
        #FIXME: il faut aussi décrémenter les metrics !
        count = models.MessageStore.objects(id__in=ids).update(completed=0)
        flash(gettext(u"%(count)s records reloaded.", count=count))

    """
    @action('sentmail',
            lazy_gettext(u'Delivery selectioned messages'),
            #lazy_gettext(u'Etes-vous sûr de vouloir déplacer ces messages dans la corbeille ?')
            )
    def action_sent_mail(self, ids):
        formdata=MultiDict(dict(ids=",".join(ids)))
        form = forms.SentMailForm(formdata=formdata)
        url_post = url_for('messagestore-all.sent_mail')
        return self.render('mmw/models/message_store/sent-mail.html', form=form, url_post=url_post)
    
    @expose('/sent-mail/', methods=('POST',))
    """
    def sent_mail(self):
        """
        TODO: Utiliser le form pour enregistrer une action/tasks à faire plus tard
        TODO: Utiliser mon client smtp avec xforward si le server implémente xforward
        TODO: enregistrer les senders refusés
        TODO: modifier le status du message: en attente de livraison
       
        http://zurb.com/ink/docs.php 
        http://www.magiksys.net/pyzmail/
        http://tomekwojcik.github.io/envelopes/
        """
        import smtplib
        form = forms.SentMailForm()
        
        if form.validate_on_submit():
            ids = form.data.get('ids', "").split(",")
            is_origin = form.data.get('is_origin', False)
            sender = form.data.get('sender', '<>')
            rcpts = form.data.get('rcpts', [])
            
            client = smtplib.SMTP('localhost', port=2500)
            client.set_debuglevel(0)
            result = {}
            for message in models.MessageStore.objects(id__in=ids):
                fromaddr = None
                toaddrs = None
                result[str(message.id)] = {}
                msg = message.parse_message(pure_string=True)
                if is_origin:
                    fromaddr = message.sender
                    toaddrs = message.rcpt
                else:
                    fromaddr = sender
                    toaddrs = rcpts
                
                result = client.sendmail(fromaddr, toaddrs, msg)
                print "result : ", result, type(result)
                #result[str(message.id)].update(result)
            
            server.quit()
        
            return redirect(url_for(".index_view"))                            
        
        return self.render('mmw/models/message_store/sent-mail.html', form=form, url_post="")

    def get_query(self):
        qs = ModelView.get_query(self)
        return qs.filter(completed=1)

class MessageStoreParsingErrorView(MessageStoreBaseView):

    action_disallowed_list = ['delete', 'untrash', 'trash', 'sentmail', 'reparse']

    column_list = ['sender',
                   'received', 
                   'rcpt', 
                   'rcpt_count',
                   'client_address',
                   'errors_count']

    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(errors_count__gte=1)

class MessageStoreNotCompletedView(MessageStoreBaseView):
    
    action_disallowed_list = ['delete', 'untrash', 'trash', 'sentmail', 'reparse']
    
    column_list = ['sender',
                   'received', 
                   'rcpt', 
                   'rcpt_count',
                   'client_address']
    
    column_filters = ('received', 'sender', 'client_address')
    
    column_searchable_list = ['sender', 'client_address']
    
    def get_query(self):
        return self.model.objects(mark_for_delete__ne=1, completed__ne=1)
    
class MessageStoreAllView(MessageStoreBaseView):
    
    column_list = MessageStoreBaseView.column_list
    #column_list.insert(2, 'queue')
    
    #action_disallowed_list = ['delete']
    
class MessageStoreIncomingView(MessageStoreBaseView):

    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['is_in']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_in=1)

class MessageStoreOutgoingView(MessageStoreBaseView):

    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['is_in']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_in=0)
    
class MessageStoreCleanView(MessageStoreBaseView):

    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['filter_result']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_spam__ne=1, is_virus__ne=1, is_banned__ne=1, is_unchecked__ne=1)

class MessageStoreSpamView(MessageStoreBaseView):
    
    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['filter_result']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_spam=1)

class MessageStoreVirusView(MessageStoreBaseView):
    """
    TODO: add function ou vue pour extraire liste de virus ?
    """
    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['filter_result']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_virus=1)
    
class MessageStoreBannedView(MessageStoreBaseView):
    
    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['filter_result']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_banned=1)
    
class MessageStoreUncheckedView(MessageStoreBaseView):
    
    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['filter_result']]

    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_unchecked=1)

class MessageStoreBounceView(MessageStoreBaseView):
    
    column_list = [l for l in MessageStoreBaseView.column_list if not l in ['is_bounce']]
    
    def get_query(self):
        qs = MessageStoreBaseView.get_query(self)
        return qs.filter(is_bounce=1)

def init_admin(app, 
               admin_app=None, 
               url='/admin',
               name=u"Mongo Mail Web",
               base_template='mmw/admin/layout.html',
               index_template='mmw/admin/dashboard.html',
               index_view=None,
               ):
    
    admin = admin_app or Admin(app,
                               url=url,
                               name=name,
                               index_view=index_view or AdminIndexView(template=index_template, 
                                                                       url=url,
                                                                       name="dashboard"), 
                               base_template=base_template, 
                               template_mode='bootstrap3')

    
    if app.config.get('DEMO_MODE', False):
        for m in [UserModelView, DomainView, MynetworkView, TransportView]:
            m.can_edit = False
            m.can_create = False
            m.can_delete = False
            if not m.action_disallowed_list:
                m.action_disallowed_list = []
            if not 'delete' in m.action_disallowed_list:
                m.action_disallowed_list.append('delete')
        
        UserModelView.form_excluded_columns = ('password',)
    
    category_catalog = "settings"# gettext(u"Settings")

    admin.add_view(DomainView(models.Domain, name=gettext(u"Internet Domains"), category=category_catalog))
    admin.add_view(MynetworkView(models.Mynetwork, name=gettext(u"Networks Allowed"), category=category_catalog))
    admin.add_view(TransportView(models.Transport, name=gettext(u"Next-hop destination"), category=category_catalog))

    admin.add_view(MessageStoreNotCompletedView(models.MessageStore, 
                                       name=gettext(u"Not Parsed Message"), 
                                       endpoint="messagestore-not-parsed",
                                       category="messages"))
    
    admin.add_view(MessageStoreParsingErrorView(models.MessageStore, 
                                       name=gettext(u"Parsing Error"), 
                                       endpoint="messagestore-parsing-error",
                                       category="messages"))    
    
    admin.add_view(MessageStoreAllView(models.MessageStore, 
                                       name=gettext(u"All messages"), 
                                       endpoint="messagestore-all",
                                       category="messages"))

    admin.add_view(MessageStoreIncomingView(models.MessageStore, 
                                       name=gettext(u"Incoming Messages"), 
                                       endpoint="messagestore-incoming",
                                       category="messages"))
    
    admin.add_view(MessageStoreOutgoingView(models.MessageStore, 
                                       name=gettext(u"Outgoing Messages"), 
                                       endpoint="messagestore-outgoing",
                                       category="messages"))
    
    
    """
    admin.add_view(MessageStoreIncomingView(models.MessageStore, 
                                            name=gettext(u"New messages"), 
                                            endpoint="messagestore-incoming", 
                                            category="messages"))
    """
    
    admin.add_view(MessageStoreCleanView(models.MessageStore, 
                                        name=gettext(u"Clean Message"), 
                                        endpoint="messagestore-clean",
                                        category="messages"))
    
    admin.add_view(MessageStoreSpamView(models.MessageStore, 
                                        name=gettext(u"Spam Message"), 
                                        endpoint="messagestore-spam",
                                        category="messages"))
    
    admin.add_view(MessageStoreVirusView(models.MessageStore, 
                                         name=gettext(u"Infected Message"), 
                                         endpoint="messagestore-virus", 
                                         category="messages"))

    admin.add_view(MessageStoreBannedView(models.MessageStore, 
                                        name=gettext(u"Banned Message"), 
                                        endpoint="messagestore-banned",
                                        category="messages"))
    
    admin.add_view(MessageStoreUncheckedView(models.MessageStore, 
                                        name=gettext(u"Unchecked Message"), 
                                        endpoint="messagestore-unchecked",
                                        category="messages"))
    
    
    admin.add_view(MessageStoreBounceView(models.MessageStore, 
                                        name=gettext(u"Bounced Message"), 
                                        endpoint="messagestore-bounced",
                                        category="messages"))

    """    
    actions_category=gettext(u"Actions")    
    
    admin.add_link(AuthenticatedMenuLink(name=gettext(u"Livrer le message"),
                                         category=actions_category,
                                         endpoint='messagestore-all.sent_mail'))
    """
    
    top_category=gettext(u"Statistics - Top N")
    
    metric_category = "metrics" #gettext(u"Metrics")
    
    admin.add_view(MetricView(name="metrics",
                              endpoint="metrics",                              
                              #category=metric_category
                              ))
    
    admin.add_view(MetricModelView(models.Metric, 
                                   name=gettext(u"All Metrics"), 
                                   category=metric_category))

    admin.add_view(MetricModelGroupView(models.Metric, 
                                   name=gettext(u"Group Metrics"),
                                   endpoint="metric-group", 
                                   category=metric_category))
    
    admin.add_view(MetricModelIPView(models.Metric, 
                                   name=gettext(u"IP Metrics"),
                                   endpoint="metric-ip", 
                                   category=metric_category))

    admin.add_view(MetricModelCountryView(models.Metric, 
                                   name=gettext(u"Country Metrics"),
                                   endpoint="metric-country", 
                                   category=metric_category))
    
    admin.add_view(MetricModelServerView(models.Metric, 
                                   name=gettext(u"Server Metrics"),
                                   endpoint="metric-server", 
                                   category=metric_category))

    admin.add_view(MetricModelDomainRefView(models.Metric, 
                                   name=gettext(u"Internal Domain Metrics"),
                                   endpoint="metric-domain-ref", 
                                   category=metric_category))

    admin.add_view(MetricModelDomainView(models.Metric, 
                                   name=gettext(u"Domain Metrics"),
                                   endpoint="metric-domain", 
                                   category=metric_category))

    admin.add_view(MetricModelDomainSenderView(models.Metric, 
                                   name=gettext(u"Domain Sender Metrics"),
                                   endpoint="metric-sender", 
                                   category=metric_category))

    admin.add_view(MetricModelDomainRecipientView(models.Metric, 
                                   name=gettext(u"Domain Recipient Metrics"),
                                   endpoint="metric-recipient", 
                                   category=metric_category))

    
    
    """
    admin.add_link(AuthenticatedMenuLink(name=gettext(u"Message by day"),
                                         category=metric_category,
                                         endpoint='metrics.group_by_day'))
    
    admin.add_link(AuthenticatedMenuLink(name=gettext(u"Message by month"),
                                         category=metric_category,
                                         endpoint='metrics.group_by_month'))
    
    admin.add_link(AuthenticatedMenuLink(name=gettext(u"Per Country"),
                                         category=top_category,
                                         endpoint='metrics.top_country_count'))
    """                                         

    #admin.add_view(RoleModelView(models.Role, name=gettext(u"Roles"), category=category_catalog))
    admin.add_view(UserModelView(models.User, name=gettext(u"Users"), category=category_catalog))
    admin.add_view(AccountMenu(name="account", endpoint="user_menu"))

    """
    TODO:
    admin.add_view(MongoSystem(name=gettext(u"MongoDB Indexes"), 
                               endpoint="mongo_sys", 
                               category=gettext(u"Tools")))
    """
    
    #admin.add_view(DomainViewTrash(models.Domain, 
    #                               name=gettext(u"Internet Domains"), 
    #                               endpoint="domain_trash",
    #                               category="trash"))
    
    #admin.add_link(AuthenticatedMenuLink(name=gettext(u"Internet Domains"),
    #                                     category="trash", #gettext(u"Trash"),
    #                                     endpoint='domain_trash.index_view'))
    
