# -*- coding: utf-8 -*-

from .extensions import gettext

MM_MODE_QUARANTINE = 1
MM_MODE_PROXY = 2
MM_MODE_FILTER = 3

SESSION_LANG_KEY = "current_lang"
SESSION_TIMEZONE_KEY = "current_tz"
SESSION_THEME_KEY = "current_theme"

MENU_ITEMS = {
    'dashboard': {
         'title': gettext(u"Dashboard"),
         'icon': "fa fa-dashboard fa-fw",
    },
    'settings': {
         'title': gettext(u"Settings"),
         'icon': "fa fa-asterisk fa-fw",
    },
    'messages': {
         'title': gettext(u"Messages"),
         'icon': "fa fa-envelope-o fa-fw",
    },
    'metrics': {
         'title': gettext(u"Metrics"),
         'icon': "fa fa-tachometer fa-fw",
    },
    'trash': {
         'title': gettext(u"Trash"),
         'icon': "fa fa-trash fa-fw",
    },
}

GROUP_DEFAULT = 'DEFAULT'

HEADER_QUARANTINE = 'X-Quarantine-ID'

HEADER_IS_VIRUS = 'X-Amavis-Alert'
HEADER_IS_BANNED = 'X-Amavis-Alert'
HEADER_IS_SPAM = 'X-Spam-Flag'
HEADER_SPAM_SCORE = 'X-Spam-Score'
HEADER_SPAM_RULES = 'X-Spam-Status'
HEADER_XMAILER = 'X-Mailer'
SEARCH_VIRUS = 'INFECTED'                #Information à rechercher dans HEADER_IS_VIRUS  
SEARCH_BANNED = 'BANNED'                    #Information à rechercher dans HEADER_IS_BANNED

HEADER_IS_UNCHECKED = 'Subject'
SEARCH_UNCHECKED = 'UNCHECKED'

HEADERS_SENDERS = ['X-Envelope-From',
                  'From',
                  'Envelope-Sender',
                  'X-Sender',
                  'Return-Path',
                  'Reply-To',
                  'Sender']

# Nom des entêtes reconnus pour contenir un ou plusieurs destinataires
HEADERS_RECIPIENTS = ['X-Envelope-To',
                      'To',
                      'Cc',
                      'Apparently-To',
                      'Envelope-Recipients',
                      'Apparently-Resent-To',
                      'Envelope-To',
                      'X-Delivered-To',
                      'X-Original-To',
                      'X-Rcpt-To',
                      'X-Real-To']

MESSAGE_QUEUE_INCOMING = 1      #Queue par défaut pour tous mail entrant
MESSAGE_QUEUE_ACTIVE = 2        #Queue pour traitement en cours (filtrage, modification, livraison, ...)
MESSAGE_QUEUE_DEFERRED = 3      #Queue d'attente suite à un problème de traitement  ou de ressource
MESSAGE_QUEUE_DELIVERY = 4      #Queue en attente de livraison
MESSAGE_QUEUE_QUARANTINE = 5    #En quarantaine - Attente de purge ou autre
MESSAGE_QUEUE_TURING = 6        #En attente Turing
MESSAGE_QUEUE_HOLD = 7          #Queue bloqué. Déblocage manuel
MESSAGE_QUEUE_DELETED = 8       #En attente de suppression
MESSAGE_QUEUE_ARCHIVED = 9      #En attente d'archivage
MESSAGE_QUEUE_ERROR = 99        #En erreur

#TODO: traduction
MESSAGE_QUEUE_CHOICES = (
    (MESSAGE_QUEUE_INCOMING, gettext(u"Default Queue for new messages")),
    #(MESSAGE_QUEUE_ACTIVE, gettext(u"Queue de traitement en cours")),
    #(MESSAGE_QUEUE_DEFERRED, gettext(u"Queue d'attente")),
    #(MESSAGE_QUEUE_DELIVERY, gettext(u"Queue d'attente de livraison")),
    (MESSAGE_QUEUE_QUARANTINE, gettext(u"In Quarantine")),
    (MESSAGE_QUEUE_TURING, gettext(u"Wait from Turing")),
    #(MESSAGE_QUEUE_HOLD, gettext(u"Queue bloqué")),
    (MESSAGE_QUEUE_DELETED, gettext(u"Queue for delete")),
    #(MESSAGE_QUEUE_ARCHIVED, gettext(u"Queue d'attente d'archivage")),
    #(MESSAGE_QUEUE_ERROR, gettext(u"Queue d'erreurs")),
)

MESSAGE_QUEUE_DICT = dict(MESSAGE_QUEUE_CHOICES)

MESSAGE_TAG_CLEAN = 'clean'
MESSAGE_TAG_SPAM = 'spam'
MESSAGE_TAG_VIRUS = 'virus'
MESSAGE_TAG_BANNED = 'banned'
MESSAGE_TAG_ARCHIVED = 'archived'

DEFAULT_LIMIT_HEADERS = [
    'Subject',
    'Date',           
]

# Nom des entêtes reconnus pour contenir un email expéditeur
HEADERS_SENDERS = ['X-Envelope-From',
                  'From',
                  'Envelope-Sender',
                  'X-Sender',
                  'Return-Path',
                  'Reply-To',
                  'Sender']

# Nom des entêtes reconnus pour contenir un ou plusieurs destinataires
HEADERS_RECIPIENTS = ['X-Envelope-To',
                      'To',
                      'Cc',
                      'Apparently-To',
                      'Envelope-Recipients',
                      'Apparently-Resent-To',
                      'Envelope-To',
                      'X-Delivered-To',
                      'X-Original-To',
                      'X-Rcpt-To',
                      'X-Real-To']


MYNETWORK_TYPE_IP = 1
MYNETWORK_TYPE_NET = 2
MYNETWORK_TYPE_HOSTNAME = 3

MYNETWORK_TYPE_CHOICES = (
    (MYNETWORK_TYPE_IP, gettext(u"IP Address")),
    (MYNETWORK_TYPE_NET, gettext(u"Network Address")),
    (MYNETWORK_TYPE_HOSTNAME, gettext(u"Hostname")),
)

METRIC_KEY_TYPE_GROUP = 1
METRIC_KEY_TYPE_IP = 2
METRIC_KEY_TYPE_COUNTRY = 3
METRIC_KEY_TYPE_DOMAIN_REF = 4
METRIC_KEY_TYPE_DOMAIN_SENDER = 5
METRIC_KEY_TYPE_DOMAIN_RECIPIENT = 6
METRIC_KEY_TYPE_DOMAIN = 7
METRIC_KEY_TYPE_SERVER = 8
METRIC_KEY_TYPE_CHOICES = (
    (METRIC_KEY_TYPE_GROUP, u'Group'),
    (METRIC_KEY_TYPE_IP, u'IP'),
    (METRIC_KEY_TYPE_COUNTRY, u'Country'),
    (METRIC_KEY_TYPE_DOMAIN_REF, u'Reference Domain'),
    (METRIC_KEY_TYPE_DOMAIN_SENDER, u'Domain Sender'),
    (METRIC_KEY_TYPE_DOMAIN_RECIPIENT, u'Domain Recipient'),
    (METRIC_KEY_TYPE_DOMAIN, u'Domain Sender or Recipient'),
    (METRIC_KEY_TYPE_SERVER, u'SMTP Server'),
)
METRIC_KEY_TYPE_CHOICES_DICT = dict(METRIC_KEY_TYPE_CHOICES)

REFRESH_TIME_5SEC = 5 * 1000
REFRESH_TIME_30SEC = 30 * 1000
REFRESH_TIME_60SEC = 60 * 1000
REFRESH_TIME_NOT = 0
REFRESH_CHOICES = (
    (REFRESH_TIME_5SEC, gettext(u"Every 5 seconds")),
    (REFRESH_TIME_30SEC, gettext(u"Every 30 seconds")),
    (REFRESH_TIME_60SEC, gettext(u"Every 60 seconds")),
    (REFRESH_TIME_NOT, gettext(u"Disabled")),
)
REFRESH_CHOICES_DICT = dict(REFRESH_CHOICES)

PERIOD_CHOICES = (
    ('today', gettext(u"Today")),
    #('yesterday', gettext(u"Yesterday")),
    ('last-24-hours', gettext(u"Last 24 hours")),
    ('last-week', gettext(u"Last Week")),
    ('last-month', gettext(u"Last Month")),
    ('last-year', gettext(u"Last Year")),
    #('last-2-year', gettext(u"Depuis 2 ans")),
    #('last-monday', gettext(u"Last Monday")),
    #('same-day-last-week', gettext(u"Même jour qu'aujourd'hui, il y a une semaine")),
)
PERIOD_CHOICES_DICT = dict(PERIOD_CHOICES)