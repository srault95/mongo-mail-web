# -*- coding: utf-8 -*-

import logging

import email
#from dateutil import parser as dateparser
from email.utils import mktime_tz, parsedate_tz
import datetime

from flanker.addresslib import address
from flanker.mime.create import from_string
from flanker.mime.message.fallback.create import from_string as recover

from mongoengine import fields
from mongoengine import NULLIFY, CASCADE, DENY, PULL
from mongoengine import OperationError, ValidationError, NotUniqueError

from flask_security.utils import encrypt_password, verify_password
from flask_security import UserMixin, RoleMixin, AnonymousUser

try:
    from flask_mongoengine import MongoEngine
    db = MongoEngine()
    Document = db.Document
    EmbeddedDocument = db.EmbeddedDocument
    DynamicDocument = db.DynamicDocument
    DynamicEmbeddedDocument = db.DynamicEmbeddedDocument
except:
    from mongoengine import Document, EmbeddedDocument, DynamicDocument, DynamicEmbeddedDocument

from . import constants
from . import utils
from . import geoip_tools
from .extensions import gettext

logger = logging.getLogger(__name__)

def get_country(client_address):
    
    if not geoip_tools.is_configured():
        logger.warn("geoip tools is not configured")
        return
    
    if not client_address:
        return None
    
    if geoip_tools.is_public_address(client_address):
        
        country_code, country_name = geoip_tools.check_country(client_address)
        
        return country_code
        

def identify(sender=None, client_address=None, rcpt=[]):
    """
    Alimente group_name, domain_name, is_in (1 ou 0)
    
    TODO: passer la liste des domaines et mynetwork à la méthode
    TODO: intégrer dans completed()
    
    """
    data = {}
    
    net = Mynetwork.objects(ip_address=client_address).first()
    
    if net:
        data['group_name'] = net.group_name
        data['is_in'] = 0
        
        if sender: 
            
            sender = address.parse(sender, addr_spec_only=True)
    
            if sender:
                domain_sender = sender.hostname #utils.parse_domain(sender)
                if domain_sender:
                    d = Domain.objects(name__iexact=domain_sender).first()
                    if d:
                        data['domain_name'] = d.name
    else:
        data['is_in'] = 1
        recipients_domain = []
        for r in rcpt:
            recipient = address.parse(r, addr_spec_only=True)
            if recipient:
                recipients_domain.append(recipient.hostname)
        
        domain = Domain.objects(name__in=recipients_domain).first()
        if domain:
            data['domain_name'] = domain.name
            data['group_name'] = domain.group_name

        #country for is_in only        
        if client_address:
            country = get_country(client_address)
            if country and len(country.strip()) > 0:
                data['country'] = country
        
    return data

def message_complete(key, message_string, sender=None):
    
    result = {
        'files': [],
        'headers': {}
    }
    
    parsing_errors = []
    errors_count = 0
    
    try:
        msg = from_string(message_string)
    except Exception, err:
        logger.error("%s:%s" % (key, str(err)))
        parsing_errors.append(str(err))
        msg = recover(message_string)
    
    try:
        #msg = from_string(message_string)
    
        if msg.subject:
            result['subject'] = msg.subject

        result['message_id'] = msg.message_id
        result['size'] = msg.size  #comprend pièces jointes + mail

        """
        size        
        V:\git\radicalspam\rs-admin\src\radicalspam\0-mail-analytics\postfix-policyng-customer\mailgun.png
            octets sur disque: 60 168
            part.size: 81 443        
        """
    except Exception, err:
        logger.error("%s:%s" % (key, str(err)))
        parsing_errors.append(str(err))

    try:    
        if msg.content_type.is_multipart():
            for part in msg.parts: 
                if not part.content_type.is_singlepart():
                    continue

                filename = part.detected_file_name
                if filename:
                    result['files'].append(MessageAttachment(filename=filename, 
                                      size=part.size,
                                      content_type=part.content_type.value #'image/png'
                                      ))

        result['files_count'] = len(result['files'])
        
    except Exception, err:
        logger.error("%s:%s" % (key, str(err)))
        parsing_errors.append(str(err))

    try:
        headers = {}        
        for key, value in msg.headers.items():
            if key in headers:
                old_value = headers[key]
                if not isinstance(old_value, list):
                    old_value = [old_value]
                headers[key] = old_value + [value]
            else:
                headers[key] = value
                
        result['headers'] = headers
        
    except Exception, err:
        logger.error("%s:%s" % (key, str(err)))
        parsing_errors.append(str(err))

    try:        
        result['is_bounce'] = 1 if utils.get_is_bounce(msg, sender=sender) else 0
        result['is_spam'] = 1 if utils.get_is_spam(msg.headers) else 0
        result['is_virus'] = 1 if utils.get_is_virus(msg.headers) else 0
        result['is_banned'] = 1 if utils.get_is_banned(msg.headers) else 0
        result['is_unchecked'] = 1 if utils.get_is_unchecked(msg.headers) else 0
        
        result['quarantine_id'] = utils.get_quarantine_id(msg.headers)
    except Exception, err:
        logger.error("%s:%s" % (key, str(err)))
        parsing_errors.append(str(err))

    try:        
        date = msg.headers.get('Date', None)
        if date:
            #print "!!!!date : ", date
            #result['sent_origin'] = date
            #result['sent'] = dateparser.parser(date)
            result['sent'] = datetime.datetime.utcfromtimestamp(mktime_tz(parsedate_tz(date)))
            """
            date.replace(' (UTC)', '')
            """
            #parser.parse(date)
            #datetime.datetime(2012, 7, 6, 12, 34, 44, tzinfo=tzoffset(None, 14400))
            #u'Fri, 6 Jul 2012 12:34:44 +0400'
            """
            utils.parsedate_tz("Mon,  9 Feb 2015 05:47:55 +0000 (UTC)")
            (2015, 2, 9, 5, 47, 55, 0, 1, -1, 0) #05H47
            
            datetime.datetime(*utils.parsedate_tz("Mon,  9 Feb 2015 05:47:55 +0000 (UTC)")[:7])
            datetime.datetime(2015, 2, 9, 5, 47, 55) : 05H47
            
            datetime.datetime.fromtimestamp(utils.mktime_tz(utils.parsedate_tz("Mon,  9 Feb 2015 05:47:55 +0000 (UTC)")))
            datetime.datetime(2015, 2, 9, 6, 47, 55) : 06H47
            
            datetime.datetime.utcfromtimestamp(utils.mktime_tz(utils.parsedate_tz("Mon,  9 Feb 2015 05:47:55 +0000 (UTC)")))
            datetime.datetime(2015, 2, 9, 5, 47, 55) : 05H47
            
            utils.parsedate_tz('Fri, 6 Jul 2012 12:34:44 +0400')
            (2012, 7, 6, 12, 34, 44, 0, 1, -1, 14400) : 12H34 
            
            datetime.datetime(*utils.parsedate_tz('Fri, 6 Jul 2012 12:34:44 +0400')[:7])
            datetime.datetime(2012, 7, 6, 12, 34, 44) : 12H34
            
            datetime.datetime.fromtimestamp(utils.mktime_tz(utils.parsedate_tz('Fri, 6 Jul 2012 12:34:44 +0400')))
            datetime.datetime(2012, 7, 6, 10, 34, 44) : 10H34
            
            datetime.datetime.utcfromtimestamp(utils.mktime_tz(utils.parsedate_tz('Fri, 6 Jul 2012 12:34:44 +0400')))
            datetime.datetime(2012, 7, 6, 8, 34, 44) : 08H34  - - 4H
            
            datetime.datetime.utcfromtimestamp(utils.mktime_tz(utils.parsedate_tz('Tue, 31 Mar 2015 17:27:49 GMT')))
            datetime.datetime(2015, 3, 31, 17, 27, 49)
            
            rs-online-mx1-20150331T231523-22702-03.gz
            Tue, 31 Mar 2015 21:14:36 +0000 (UTC)
            
            datetime.datetime(*utils.parsedate_tz(date)[:7])
            datetime.datetime(2012, 7, 6, 12, 34, 44)    #12h34

            utils.mktime_tz(utils.parsedate_tz(date))
            1341563684                        
                                    
            datetime.datetime.fromtimestamp(utils.mktime_tz(utils.parsedate_tz(date)))
            datetime.datetime(2012, 7, 6, 10, 34, 44)    #10h34
            
            email.utils:
            utils.parsedate('Mon,  9 Feb 2015 05:47:55 +0000 (UTC)')
            (2015, 2, 9, 5, 47, 55, 0, 1, -1)
            
            utils.parsedate_tz('Mon,  9 Feb 2015 05:47:55 +0000 (UTC)')
            (2015, 2, 9, 5, 47, 55, 0, 1, -1, 0)
            
            utils.parsedate_tz(u'Fri, 6 Jul 2012 12:34:44 +0400')
            (2012, 7, 6, 12, 34, 44, 0, 1, -1, 14400)
            
            utils.parsedate(u'Fri, 6 Jul 2012 12:34:44 +0400')
            (2012, 7, 6, 12, 34, 44, 0, 1, -1)                        
            """
        
    except Exception, err:
        logger.error("%s:%s" % (key, str(err)))
        parsing_errors.append(str(err))
        
    result['parsing_errors'] = parsing_errors
    result['errors_count'] = len(parsing_errors)
     
    return result

def clean_ip_network(value, field_name=None):
    """
    TODO: A revoir. essayer en utilisant la valeur numérique ou hexa ?
    
    from ipaddr import IPv4Network as ip_interface
    unicode(ip_interface('{0}/24'.format('192.168.0.1')).network)
    u'192.168.0.0'
    
    IPy.IP('192.168.0.1').len()
    1
    
    IPy.IP('192.168.0.0').len()
    1
    
    IPy.IP('192.168.0.0/24').len()
    256    
    """

def clean_ip_address(value, field_name=None):
    u"""
    Valide une adresse IP

    :param str value: Adresse IP à valider
    :param field_name: Nom du champs dans lequel se trouve la valeur
    :type field_name: str or None
    :return: Une exception si le format est invalide
    :rtype: ValidationError or None
    :raises ValidationError: if l'adresse IP est invalide
    """
    
    #TODO: Ajout interdire ip interne et/ou private
    #TODO: Liste de network qu'il ne faut pas mettre en BL (dans Settings)
    
    valid = False
    
    if value:
        valid = utils.check_ipv4(value) or utils.check_ipv6(value)

    if not valid:
        message = gettext(u"Adresse IP invalide: %s" % value)
        raise ValidationError(message, field_name=field_name)

def clean_domain(value, field_name=None):
    
    new_value = "user@%s" % value

    if not fields.EmailField.EMAIL_REGEX.match(new_value):
        message = gettext(u"Internet Domain: %s" % value)
        raise ValidationError(message, field_name=field_name)

def clean_email(value, field_name=None):
    
    if not fields.EmailField.EMAIL_REGEX.match(value):
        message = gettext(u"Invalid Email Address: %s" % value)
        raise ValidationError(message, field_name=field_name)

def clean_hostname(value, field_name=None):
    """Validation du format FQDN d'un nom d'hôte"""

    """
    Voir : (?=^.{1,254}$)(^(?:(?!\d+\.)[a-zA-Z0-9_\-]{1,63}\.?)+(?:[a-zA-Z]{2,})$)
        1) Entire fqdn less than 255 chars.
        2) Host and domain names may contain an underscore.
            Peut contenir des _
        3) 1st char can be a number.
            Le premier caractère peut ou ne peut pas être un chiffre ?
        4) No part can be all numbers.
        5) Allows any TLD Works in C#

        allowed = re.compile("(?=^.{1,254}$)(^(?:(?!\d+\.)[a-zA-Z0-9_\-]{1,63}\.?)+(?:[a-zA-Z]{2,})$)", re.IGNORECASE)

    Voir : (?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)
        1) Entire fqdn less than 255 chars.
        2) Host and domain names may contain an underscore.
        3) 1st char can be a number.
        4) No part can be all numbers.
        5) Allows any TLD Works in C#.

        allowed = re.compile("(?=^.{1,254}$)(^(?:(?!\d+\.|-)[a-zA-Z0-9_\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)", re.IGNORECASE)

        allowed = re.compile("(?=^.{1,254}$)(^(?:(?!\d|-)[a-zA-Z0-9\-]{1,63}(?<!-)\.?)+(?:[a-zA-Z]{2,})$)", re.IGNORECASE)

        reg_received    = re.compile(r'^.*\[(?P<host_ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\].*')

        regexp_fqdn = re.compile(r'^((.*)\.(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6})){5,254}$')


    >>> vals = 'toto.smtp.radicalspam.org'.split(".")
    >>> vals[(len(vals)-2):(len(vals))]
    ['radicalspam', 'org']
    >>> vals[0:(len(vals)-2)]
    ['toto', 'smtp']

    >>> vals = 'smtp.radicalspam.org'.split(".")
    >>> vals[(len(vals)-2):(len(vals))]
    ['radicalspam', 'org']
    >>> vals[0:(len(vals)-2)]
    ['smtp']

    """

    message = gettext(u"Invalid Hostname %s" % value)
    
    # TODO: V2 - Gérer idna

    # http://tools.ietf.org/html/rfc1035
    """
    - 3 partie minimum et séparés par des .
    - Partie domaine <= 63 caractères
    - Total du fqdn <= 255 catactères
    - 1er char peut être un nombre
    - Le nom d'hote et le domain peuvent contenir un _
    """
    
    if value is None or len(value.strip()) == 0:
        raise ValidationError(message, field_name=field_name)

    if len(value) > 255:
        raise ValidationError(message, field_name=field_name)

    vals = value.split(".")

    if len(vals) < 3:
        raise ValidationError(message, field_name=field_name)

    domain = ".".join(vals[(len(vals) - 2):(len(vals))])
    # host = ".".join(vals[0:(len(vals)-2)])

    if len(domain) > 63:
        raise ValidationError(message, field_name=field_name)

    # TODO: V1 - Valider que le TLD du domain existe


class BaseDocument(Document):

    #def get_store(self):
    #    pass
    """
    A utiliser pour des besoins interne comme
        1: données de démo
        2: ?
    """
    internal_field = fields.IntField(default=0)
    
    mark_for_delete = fields.IntField(default=0)
        
    def get_pk(self):
        return self.pk()
    
    def as_dict(self):
        return self.to_mongo().to_dict()    
    
    def as_json(self):
        return self.to_json()
    
    meta = {
        'abstract': True,
    }

class Counter(BaseDocument):
    #TODO cache
    
    name = fields.StringField(max_length=80, unique=True, required=True)
    
    value = fields.IntField(default=0)
    
    last_update = fields.DateTimeField(default=utils.timestamp)
    
    def __unicode__(self):
        return self.name

    meta = {
        'collection': 'counter',
        'indexes': ['name'],
        'ordering': ['name']
    }

class Role(BaseDocument, RoleMixin):
    
    name = fields.StringField(required=True, unique=True, max_length=80)
    
    active = fields.BooleanField(default=True)
    
    comments = fields.StringField(max_length=256)
    
    def __unicode__(self):
        return self.name

    meta = {
        'collection': 'role',
        'indexes': ['name'],
    }

class User(BaseDocument, UserMixin):
    """
    flask_security:
        - rend obligatoire l'auth par email
        find_user(email=auth.username)
    """
    group_name = fields.StringField(required=True, max_length=80, default=constants.GROUP_DEFAULT)
    
    #TODO: setting sur max_length
    email = fields.EmailField(max_length=255, required=True, unique=True)

    #TODO: sup limite taille et settings
    #len([a for a in '$pbkdf2-sha512$19000$AsBYi7F2bg1BqDVGiHGOkQ$RjXZvt3F0OfxR5ALyb5cTMwBXtFYdVyl4W8O7RxUSfCWsxTM6q7BMg5IPCr9kMYRyb7mIRPYZKsSSs6ICb8KQA'])
    #130 char
    password = fields.StringField(max_length=255, required=True)

    active = fields.BooleanField(default=True)
    
    confirmed_at = fields.DateTimeField()

    last_login_at = fields.DateTimeField()
    current_login_at = fields.DateTimeField()
    last_login_ip = fields.StringField(max_length=255)
    current_login_ip = fields.StringField(max_length=255)
    login_count = fields.IntField()
    
    roles = fields.ListField(fields.ReferenceField(Role, reverse_delete_rule=DENY), default=[])

    def get_roles_list(self):
        return [role.name for role in self.roles]
    
    @property
    def username(self):
        return self.email

    def password_check(self, password_clear):
        return verify_password(password_clear, self.password)
    
    def password_set(self, password_clear):
        self.password = encrypt_password(password_clear)
        return self.password

    @classmethod
    def create_user(cls, username=None, password=None, role=None, group=None):
        """Helpers for create user with exist or not exist role/group"""
        
        exist = cls.objects(email__exact=username).first()
        if exist:
            return exist
        
        r, created = Role.objects.get_or_create(name=role)
        
        user = cls(email=username, roles=[r])
        user.password_set(password)
        
        return user.save()    
        
    
    def __unicode__(self):
        return self.username

    meta = {
        'collection': 'user',
        'indexes': ['email', 'roles'],
    }
        


class Domain(BaseDocument):
    """
    TODO: Voir setting pour synchro Mailbox par LDAP ou autres
    
    TODO: Fournir api REST pour que client alimente ses domains/mailbox ?
    
    TODO: Prévoir tunnel SSH reverse ou normal pour sécurisé lien avec architecture client
    """

    group_name = fields.StringField(required=True, max_length=80, default=constants.GROUP_DEFAULT)
    
    name = fields.StringField(max_length=63, required=True, unique=True)
    
    def clean(self):
        BaseDocument.clean(self)
        clean_domain(self.name, field_name="name")
        
    def save(self, **kwargs):
        self.name = self.name.lower()
        return BaseDocument.save(self, **kwargs)
            
    def __unicode__(self):
        return self.name
    
    meta = {
        'collection': 'domain',
        'indexes': ['group_name', 'name'],
        'ordering': ['name']
    }
    
class Mynetwork(BaseDocument):
    """
    TODO: interdire loopback par un validateur ?
    FIXME: il faut pouvoir entrer IP OU NET ou que NET avec /32 quand ip
    
    TODO: Il faut un mynetwork capable d'autoriser des noms MX et des .net ?
        - plus simple d'utiliser startwith
    """

    group_name = fields.StringField(required=True, max_length=80, default=constants.GROUP_DEFAULT)
    
    address_type = fields.IntField(choices=constants.MYNETWORK_TYPE_CHOICES, 
                                   default=constants.MYNETWORK_TYPE_IP)

    ip_address  = fields.StringField(max_length=100,                                     
                                     unique=True,
                                     required=True,
                                     #not_loopback=True,
                                     verbose_name=gettext(u'IP Address'),
                                     help_text=gettext(u"Enter an IP address. ex: 192.168.1.20 in ipv4 or ipv6 format"))
    #Entrez une adresse IP au format individuel (192.168.1.20) version ipv4 ou ipv6

    comments = fields.StringField(max_length=100)
    
    def clean(self):
        """
        ip_address__istartswith=
        """
        super(Mynetwork, self).clean()

        if self.address_type == constants.MYNETWORK_TYPE_IP:
            clean_ip_address(self.ip_address, field_name="ip_address")
        elif self.address_type == constants.MYNETWORK_TYPE_NET:
            clean_ip_network(self.ip_address, field_name="ip_address")
        elif self.address_type == constants.MYNETWORK_TYPE_HOSTNAME:
            clean_hostname(self.ip_address, field_name="ip_address")
            
        
    meta = {
        'collection': 'mynetwork',
        'indexes': ['group_name', 'ip_address'],
        'ordering': ['ip_address']
    }
    
    def __unicode__(self):
        return self.ip_address

    
class Transport(BaseDocument):
    """
    TODO: Gérer options TLS pour connections avec le client
    
    Détailler besoin de connection pour auth comme gmail, ...    
    """
    group_name = fields.StringField(required=True, max_length=80, default=constants.GROUP_DEFAULT)

    #format libre smtp:...
    #TODO: validator
    #TODO: unique with domain ?
    address = fields.StringField(required=True, unique=True)
    
    comments = fields.StringField(max_length=100)

    meta = {
        'collection': 'transport',
        'indexes': ['group_name', 'address'],
    }
    
    def __unicode__(self):
        return self.address

class MessageEvent(EmbeddedDocument):

    event_date = fields.DateTimeField(default=utils.timestamp)

    #TODO: choice    
    event_type = fields.IntField()
    
    event_error = fields.IntField(default=0)
    
    event_comments = fields.StringField()
    
    event_args = fields.DictField(default={})
    

class MessageTuring(EmbeddedDocument):
    """
    
    Scénarios:
        0. Impossibilité turing
            - Pas de destinataire valide (from/x-from...)
        
        1. Envoi d'un mail de vérification
            - Mail délivré OK
            - Mail non délivré
                - Erreur 5xx
                - Erreur 4xx
        
        2a. Débloquage par confirmation expéditeur
        
        2b. Débloquage par anulation turing par destinataire ou admin
        
        2c. Dépassement de délai
        
        N. Ajout info turing au rapport quotidien envoyé au destinataire
    
    Document créé quand un MessageStore est placé en turing queue = MESSAGE_QUEUE_TURING
    
    TODO: Action/Tâche d'envoi de mail à l'expéditeur
    
    TODO: Envoi de mail récapitulatif au(x) destinataire ?
    
    TODO: Actions suite à validation : 
    
    - Ajout de l'expéditeur (email ?, domain ?, ip ?) en liste blanche
    - Livrer le mail
    - Marquer pour purge le mail et le turing
    """

    key = fields.StringField(required=True)
    
    created_date = fields.DateTimeField(default=utils.timestamp)
    
    #durée de validité ? A calculer selon settings
    mail_date = fields.DateTimeField()

    #TODO: mettre dans constants
    mail_status = fields.IntField(choices=(
                                    (0, gettext(u"Unsent")),
                                    (1, gettext(u"Sent")),
                                    (2, gettext(u"Unrecoverable error")),
                                    (3, gettext(u"Temporary error")),
                                    (9, gettext(u"Turing canceled")),
                                ))
    
    valid_date = fields.DateTimeField(verbose_name=gettext(u"Validation Date"))
    
    #IP à partir de laquelle le turing à été validé
    valid_ip = fields.StringField() 

    def __unicode__(self):
        return self.key
    

class MessageAttachment(EmbeddedDocument):
    
    filename = fields.StringField()
    
    size = fields.IntField(default=0)
    
    content_type = fields.StringField()
        
class MessageStore(BaseDocument):
    """
    TODO: is_spam, is_virus, ... en champs numérique: 0 ou 1 pour stats
    TODO: is_ham, is_spam, ...
    
    0-prod\rs-admin\archives\rs-admin\rs_admin\mail_parser_utils.py
    
    TODO: ('X-Originating-IP', '[88.175.183.38]')
    """
    
    completed = fields.IntField(default=0)
    
    group_name = fields.StringField(required=True, max_length=80,
                                    default=constants.GROUP_DEFAULT,
                                    verbose_name=gettext(u"Group"))
    
    domain_name = fields.StringField(max_length=63,
                                     verbose_name=gettext(u"Domain"))
    
    policy_uid = fields.StringField()
    
    quarantine_id = fields.StringField()
    
    is_in = fields.IntField(default=1,
                            verbose_name=gettext(u"Incoming message"),
                            help_text=gettext(u"Incoming or Outgoing Message"))

    store_key = fields.StringField(required=True, unique=True)

    sent = fields.DateTimeField(verbose_name=gettext(u"Sent Date"))
        
    #sent_origin = fields.StringField()
        
    received = fields.DateTimeField(default=utils.timestamp, 
                                    verbose_name=gettext(u"Received Date"))
    
    headers = fields.DictField()
    
    message = fields.FileField()
    
    #FIXME: ne pas utiliser le nom size !!!!
    size = fields.LongField(default=0, 
                            verbose_name=gettext(u"Size"))

    subject = fields.StringField(verbose_name=gettext(u"Subject"))
    
    message_id = fields.StringField()
    
    sender = fields.StringField(verbose_name=gettext(u"Sender"))
    
    #Pas de EmailField
    rcpt = fields.ListField(fields.StringField(), default=[],
                            verbose_name=gettext(u"Recipients(s)"))
    
    rcpt_count = fields.IntField(default=0,
                                 verbose_name=gettext(u"Rcpts"),
                                 help_text=gettext(u"Number of recipients"))
    
    #mode proxy ou autre pour rcpt refusé à la livraison - refus partiel seulement
    rcpt_refused = fields.DictField(default={})
    
    #IP du client original par xforward
    client_address = fields.StringField(verbose_name=gettext(u"IP Address"))
    
    country = fields.StringField(verbose_name=gettext(u"Country"),
                                 help_text=gettext(u"Country based on ip address of sender smtp"))
    
    #receiveds_header = fields.SortedListField(fields.StringField(), default=[])
    
    is_bounce = fields.IntField(default=0,
                                verbose_name=gettext(u"Bounce ?"))

    is_spam = fields.IntField(default=0, 
                              verbose_name=gettext(u"Spam ?"))
    
    is_virus = fields.IntField(default=0,
                               verbose_name=gettext(u"Infected ?"))
    
    is_banned = fields.IntField(default=0,
                                verbose_name=gettext(u"Banned ?"))
    
    is_unchecked = fields.IntField(default=0,
                                   verbose_name=gettext(u"Checked ?"))

    xforward = fields.DictField()

    #IP du serveur SMTP postfix    
    server = fields.StringField()
    
    queue = fields.IntField(choices=constants.MESSAGE_QUEUE_CHOICES, 
                            default=constants.MESSAGE_QUEUE_INCOMING)

    files_count = fields.IntField(default=0,
                                  verbose_name=gettext(u"Files"),
                                  help_text=gettext(u"Number of attachments in message"))
    
    files = fields.EmbeddedDocumentListField(MessageAttachment)
    
    events = fields.EmbeddedDocumentListField(MessageEvent)
    
    tags = fields.ListField(fields.StringField(), default=[])

    parsing_errors = fields.ListField(fields.StringField(), default=[])

    errors_count = fields.IntField(default=0)
    
    turing = fields.EmbeddedDocumentField(MessageTuring, required=False)
    
    metric = fields.IntField(default=0)
    
    def get_filter_result(self):
        if self.is_virus:
            return "VIRUS"
        elif self.is_spam:
            return "SPAM"
        elif self.is_banned:
            return "BANNED"
        elif self.is_unchecked:
            return "UNCHECKED"
        else:
            return "CLEAN"
        
    
    filter_result = property(fget=get_filter_result)
    
    def _complete(self):
        """
        Complete parsing message
        """
        
        values = {'completed': 1}
            
        other_fields = message_complete(self.store_key, 
                                        self.parse_message(pure_string=True), 
                                        sender=self.sender)
        
        values.update(other_fields)
        
        values.update(identify(sender=self.sender, 
                               client_address=self.client_address, 
                               rcpt=self.rcpt))
        
        fields = MessageStore._fields.keys()
        for key, value in values.iteritems():
            if key in fields:
                setattr(self, key, value)
            
        #TODO: validate / clean
        return self.save(force_insert=False)#, validate, clean, write_concern, cascade, cascade_kwargs, _refs, save_condition)
            
    def parse_message(self, pure_string=False):
        msg_string = utils.uncompress(self.message.read())
        try:
            if pure_string:
                return msg_string
            return from_string(msg_string)
        except Exception, err:
            logger.error(str(err))
            return recover(msg_string)
        
    def __unicode__(self):
        return self.store_key
    
    meta = {
        'collection': 'message',
        'indexes': [
            'group_name',
            'domain_name',
            'policy_uid',
            'quarantine_id',
            'client_address',
            'country',
            'store_key', 
            '-received',
            'sent', 
            'server',
            'queue',
            'subject',
            'sender',
            'rcpt',
            'message_id',
            'files',
            ['-received', 'sender', 'rcpt', 'subject'],            
        ],
        'ordering': ['-received']
            
    }
    
class Setting(Document):
    
    is_global = fields.BooleanField(default=False)
    
    per_page = fields.IntField(default=10)
    
    theme = fields.StringField()
    
    username = fields.StringField()
    
    lang = fields.StringField()

    tz = fields.StringField()

class MetricKeys(EmbeddedDocument):
    
    count = fields.LongField(default=0)
    
    mail_in = fields.LongField(default=0)
    
    mail_out = fields.LongField(default=0)
    
    clean = fields.LongField(default=0)
    
    spam = fields.LongField(default=0)
    
    virus = fields.LongField(default=0)
    
    banned = fields.LongField(default=0)
    
    unchecked = fields.LongField(default=0)
    
    bounce = fields.LongField(default=0)
    
    files_count = fields.LongField(default=0)
    
    total_size = fields.LongField(default=0.0)

class Metric(Document):
    """
    key:
        address IP
    """
    version = fields.IntField(default=0)
    
    internal_field = fields.IntField(default=0)
    
    group_name = fields.StringField(required=True, max_length=80, default=constants.GROUP_DEFAULT)
    
    date = fields.DateTimeField(required=True) 
    
    key = fields.StringField(required=True)
    
    key_type = fields.IntField(choices=constants.METRIC_KEY_TYPE_CHOICES, default=constants.METRIC_KEY_TYPE_GROUP)
    
    metrics = fields.EmbeddedDocumentField(MetricKeys)
    
    meta = {
        'collection': 'metric',
        'indexes': ['group_name', 'key', 'key_type', 'metrics'],
        'ordering': ['-date']#, 'key_type', 'key']
    }
    
