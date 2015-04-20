# -*- coding: utf-8 -*-

import os
from wtforms import *
from flask_wtf.form import Form, _is_hidden
from wtforms import fields, widgets

from flask_admin.model.fields import InlineFormField, InlineFieldList

from . import countries
from . import constants
from . import models

class WidgetProxy(object):
    '''
    Permet d'envelopper un Widget pour lui passer des paramètres qui seront executé au call, dans le render final
    '''
    
    def __init__(self, widget, **kwargs):
        self.widget = widget
        self.kwargs = kwargs

    def __getattr__(self, name):
        return getattr(self.widget, name)

    def __call__(self, field, **kwargs):
        #print "kwargs : ", kwargs
        #{'class': 'form-control'}
        kwargs.update(self.kwargs)
        return self.widget(field, **kwargs)


class BootstrapDatePickerWidget(widgets.TextInput):
    js_format = 'dd/mm/yyyy'
    
    def __init__(self, js_format = None):
        if js_format:
            self.js_format = js_format
        
    def __call__(self, field, **kwargs):
        value = kwargs.get('value', field._value())
        return u""" \
          <div class="input-group date datepicker">
          <span class="input-group-addon"><span class="glyphicon glyphicon-th"></span></span>
           <input class="form-control" type="text" data-date-format="{format}" name="{name}" id="{name}" data-date="{date}">
          </div>
        """.format(name=field.name, format=self.js_format, date=value)
        
class SearchForm(Form):
    
    date_choice = fields.SelectField(u"Quelle date",
                                     default="received",
                                    choices=(('sent', u"Date d'envoi"), ('received', u"Date de réception") )
                                    )
    
    start_date = fields.DateField(u"Du : ",
                                  format='%d/%m/%Y',
                                  #widget=BootstrapDatePickerWidget(),
                                  validators=[validators.Optional()])
    
    end_date = fields.DateField(u"Au : ",
                                format='%d/%m/%Y',
                                #widget=BootstrapDatePickerWidget(),
                                validators=[validators.Optional()])
    
    sender = fields.StringField(label=u"Expéditeur")

    rcpt = fields.StringField(label=u"Destinataire")
    
    subject = fields.StringField(label=u"Sujet")

    client_address = fields.StringField(label=u"Adresse IP")
    
    country = fields.SelectMultipleField(label=u"Pays",
                                 #choices=[('',u"Choisissez un pays")] + list(countries.COUNTRIES),
                                 choices=countries.COUNTRIES,
                                 validators=[validators.Optional()])
    
    queue = fields.SelectField(label=u"Queue",
                               coerce=int,
                               choices=constants.MESSAGE_QUEUE_CHOICES,
                               validators=[validators.Optional()])
        
class SentMailForm(Form):
    
    ids = fields.HiddenField()
    
    is_origin = fields.BooleanField(label=u"Expéditeur et destinataires originaux")
    
    sender = fields.StringField(label=u"Expéditeur")
    
    rcpts = InlineFieldList(StringField(u"Destinaires"))
    
class DomainImportForm(Form):
    
    domains = fields.TextAreaField(validators=[validators.DataRequired()])
    
    def validate_domains(form, field):
        datas = field.data.split(os.linesep)
        errors = []
        for data in datas:
            try:
                if data and len(data.strip()) > 0:
                    data = data.strip()
                    models.clean_domain(data, 'domains')
                    found = models.Domain.objects(name__iexact=data).first()
                    if found:
                        errors.append(data)
                    
            except Exception, err:
                raise ValidationError(str(err))
        
        if len(errors) > 0:
            raise ValidationError("Domains [%s] already exists" % ",".join(errors))
        