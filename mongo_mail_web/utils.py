# -*- coding: utf-8 -*-

import operator
import base64
import zlib
import json
import re
import logging
from datetime import datetime
from email.utils import parseaddr

from IPy import IP
from dateutil import tz

from . import constants

logger = logging.getLogger(__name__)

reg_received = re.compile(r'^.*\[(?P<host_ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\].*')

def percent_calcul(current, before, fieldname):
    """
    :current: dict
    :before: dict
    :fieldname: str
    
    Va: Arrival Value
    Vd: Depart Value            
    ((Va-Vd)/Vd)*100
    """
    
    va = current[fieldname]
    vd = before[fieldname]
    
    try:
        #((Va-Vd)/Vd)*100
        return (operator.truediv((va - vd), vd))*100
    except:
        return 0


#TODO: voir benchmark - time et storage: http://tukaani.org/lzma/benchmarks.html
def compress(data):
    return base64.b64encode(zlib.compress(data))

def uncompress(data):
    return zlib.decompress(base64.b64decode(data))

def check_ipv4(value):
    try:
        return IP(value).version() == 4 
    except:
        return False

def check_ipv6(value):
    try:
        return IP(value).version() == 6 
    except:
        return False


def is_public_address(address):
    try:
        return IP(address).iptype() == 'PUBLIC'
    except:
        return False

def timestamp():
    dt = datetime.utcnow()
    return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz.tzutc())

def parse_received(receives, 
                   exclude=['127.0.0.1', '::1']):
    """Récupération et parsing des champs Received"""
    
    if not receives:
        return []

    objects = []

    i=0
    for receive in receives:

        try:

            r = receive.replace('\t', ' ').replace('\n', ' ').strip()

            f = r[:4].lower()

            if (f.find('by') < 0) and (f.find('from') < 0): continue

            if (r.find('[') < 0) or (r.find(']') < 0): continue

            #Baruwa:
            #re.compile(r'(^Received:|X-Originating-IP:)')
            
            #Moi:
            #re.compile(r'^.*\[(?P<host_ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\].*')
            m = reg_received.match(r)
            
            if not m:
                logger.warning("process_received - regexp None : %s" % r )
                continue

            host_ip = m.group('host_ip')

            if host_ip is None:
                logger.warning("process_received - host_ip None : %s" % r )
                continue
            
            if host_ip in exclude:
                continue
            
            if not is_public_address(host_ip):
                continue
            
            try:
                #date_receive_str = r.split(';')[1].strip()
                
                #TOOD: Optimisations
                #date_receive = normalize_datetime(email.utils.parsedate( date_receive_str ))
                objects.append(host_ip)
                """
                        dict(host_ip=host_ip,
                             host_name=None, # TODO: StatMailReceived.host_name pas implémenté ???
                             date_receive=date_receive,
                             order_sort=i ))
                """
                
            except Exception, err:
                logger.warning("process_received - err1[%s] : %s"  % (str(err), r))

            i=i+1
            
        except Exception, err:
            logger.warning("process_received - err2[%s] : %s"  % (str(err), r))
            
    return objects

def get_quarantine_id(headers):
    """
    X-Quarantine-ID: <k54m-OMYr-Jw>
    parseaddr('<k54m-OMYr-Jw>')
    ('', 'k54m-OMYr-Jw')        
    """
    if constants.HEADER_QUARANTINE:
        v = headers.get(constants.HEADER_QUARANTINE, '')
        addr = parseaddr(v)
        if addr and len(addr) == 2:
            id = addr[1] 
            if id and len(id) > 0:
                return id

def get_is_bounce(msg, sender=None):
    """
    content_type = multipart/report
    
    Sender commençant par prvs=
        BATV rien à voir avec les bounce: c'est pour générer un tag de signature sur les mails sortant
        pour chaque recipient
    
        prvs=tag-value=mailbox@example.com
        http://en.wikipedia.org/wiki/Bounce_Address_Tag_Validation
            BATV
            http://babel.de/batv.html
    
    """
    if not sender:
        return True
    
    if sender in ["", "<>"]:
        return True
    
    if msg.content_type.value.lower() in ['multipart/report', 'message/delivery-status']:
        return True
    
    if msg.content_type.is_multipart():
        for part in msg.parts: 
            if part.content_type.value.lower() in ['multipart/report', 'message/delivery-status']:
                return True
    
    return False

def get_is_spam(headers):
    """Champs X-Spam-Flag"""
    
    if constants.HEADER_IS_SPAM in headers:
        v = headers.get(constants.HEADER_IS_SPAM, '')
        if v.strip().upper() == 'YES':
            return True

    return False


def get_is_banned(headers):
    """Champs X-Amavis-Alert"""
    
    if constants.HEADER_IS_BANNED in headers:
        value = headers.get(constants.HEADER_IS_BANNED, '')
        # TODO: IMPORTANT Récupérer liste banned
        if constants.SEARCH_BANNED in value:
            return True

    return False


def get_is_virus(headers):
    """Champs X-Amavis-Alert"""
    
    if constants.HEADER_IS_VIRUS in headers:

        value = headers.get(constants.HEADER_IS_VIRUS, '')

        if constants.SEARCH_VIRUS in value: 
            return True

    return False

def get_is_unchecked(headers):
    if constants.HEADER_IS_UNCHECKED in headers:
        value = headers.get(constants.HEADER_IS_UNCHECKED, '')
        if constants.SEARCH_UNCHECKED in value: 
            return True

    return False


