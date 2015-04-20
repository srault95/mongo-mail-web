# -*- coding: utf-8 -*-

"""
TODO: Comment gérer stats après suppression des données qui ont servi pour les produires
TODO: Notion de datetime important pour chaque stats ?
"""

import logging
import time
import datetime
from operator import itemgetter

from bson.code import Code
from dateutil import tz

from flanker.addresslib import address

from . import models
from . import constants

logger = logging.getLogger(__name__)

"""
models.Metric.objects(key_type=3, key='FR').sum('metrics.count')
12.0

- Aggrégation par heure, jour, month ?
"""

from mongoengine.queryset import transform

lock = None

def get_domain(email):
    try:
        clean = address.parse(email, addr_spec_only=True)
        if clean:
            return clean.hostname.lower()
    except:
        pass

def get_domains(emails=[]):
    values = []
    for email in emails:
        domain = get_domain(email)
        if domain:
            values.append(domain)
    return list(set(values))  

def to_utc_datetime(year=0, month=0, day=0, hour=0, minute=0, **kwargs):
    if month == 0:
        month =1
    if day == 0:
        day = 1
    return datetime.datetime(year, month, day, hour, minute, 0, 0, tzinfo=tz.tzutc())

def update_metrics_one(doc, replace_minute=True, decrement=False):
    
    if replace_minute:
        _date = doc.received.replace(minute=0, second=0, microsecond=0)
    else:
        _date = doc.received.replace(second=0, microsecond=0)
    kwargs = {}
    kwargs['inc__metrics__count'] = 1
    
    kwargs['inc__metrics__total_size'] = doc.size
    
    if doc.is_in == 1:
        kwargs['inc__metrics__mail_in'] = 1
    else:
        kwargs['inc__metrics__mail_out'] = 1

    is_clean = True
    if doc.is_spam == 1:
        kwargs['inc__metrics__spam'] = 1
        is_clean = False
    if doc.is_virus == 1:
        kwargs['inc__metrics__virus'] = 1
        is_clean = False
    if doc.is_banned == 1:
        kwargs['inc__metrics__banned'] = 1
        is_clean = False
    if doc.is_unchecked == 1:
        kwargs['inc__metrics__unchecked'] = 1
        is_clean = False
    if doc.is_bounce == 1:
        kwargs['inc__metrics__bounce'] = 1
    if is_clean:
        kwargs['inc__metrics__clean'] = 1
                
    kwargs['inc__metrics__files_count'] = doc.files_count
        
    #print transform.update(models.Metric, **kwargs)
    #{'$inc': {'metrics': {'$size': 636L}, 'metrics.mail_in': 1, 'metrics.count': 1}}
    #return
    metrics = []

    metrics.append({
        'query': dict(date=_date, key=doc.group_name, key_type=constants.METRIC_KEY_TYPE_GROUP, group_name=doc.group_name),
        'kwargs': kwargs
    })
    
    if doc.client_address:
        metrics.append({
            'query': dict(date=_date, key=doc.client_address, key_type=constants.METRIC_KEY_TYPE_IP, group_name=doc.group_name),
            'kwargs': kwargs
        })
    
    if doc.is_in:
        country = "NULL"
        if doc.country:
            country = doc.country
        metrics.append({
            'query': dict(date=_date, key=country, key_type=constants.METRIC_KEY_TYPE_COUNTRY, group_name=doc.group_name),
            'kwargs': kwargs
        })
        
    if doc.domain_name:
        metrics.append({
            'query': dict(date=_date, key=doc.domain_name, key_type=constants.METRIC_KEY_TYPE_DOMAIN_REF, group_name=doc.group_name),
            'kwargs': kwargs
        })

    if doc.server:
        metrics.append({
            'query': dict(date=_date, key=doc.server, key_type=constants.METRIC_KEY_TYPE_SERVER, group_name=doc.group_name),
            'kwargs': kwargs
        })
    
    domain_sender = None
    if doc.sender:
        domain_sender = get_domain(doc.sender)
        if domain_sender:
            metrics.append({
                'query': dict(date=_date, key=domain_sender, key_type=constants.METRIC_KEY_TYPE_DOMAIN_SENDER, group_name=doc.group_name),
                'kwargs': kwargs
            })
            metrics.append({
                'query': dict(date=_date, key=domain_sender, key_type=constants.METRIC_KEY_TYPE_DOMAIN, group_name=doc.group_name),
                'kwargs': kwargs
            })
    
    recipients_domains = get_domains(doc.rcpt)
    for r in recipients_domains:
        if domain_sender and r == domain_sender:
            continue
        
        metrics.append({
            'query': dict(date=_date, key=r, key_type=constants.METRIC_KEY_TYPE_DOMAIN_RECIPIENT, group_name=doc.group_name),
            'kwargs': kwargs
        })
        metrics.append({
            'query': dict(date=_date, key=r, key_type=constants.METRIC_KEY_TYPE_DOMAIN, group_name=doc.group_name),
            'kwargs': kwargs
        })
    
    for metric in metrics:
        query = metric['query']
        kwargs = metric['kwargs']
        if decrement:
            new_kwargs = {}
            for key, value in kwargs.iteritems():
                new_kwargs[key] = -value 
            kwargs = new_kwargs
            models.Metric.objects(**query).update_one(upsert=False, **kwargs) 
        else:
            models.Metric.objects(**query).update_one(upsert=True, **kwargs)


def update_metrics(qs=None, replace_minute=True, **query):
    """
    Solutions lock:
        - Lock et Rlock ne fonctionne pas si pas dans la même vm (run command et timer ou 2 timers)
        - Ajouter un numéro de version aux metrics finale ?
        - utiliser un verrou dans une DB mais bloque sur 1 run 
        - verrouiller chaque doc individuellement au début et à la fin
            - Dans cache générique
    """
    
    logger.debug('START update_metrics task')

    with lock('update_metrics', 'worker-once', expire=None, timeout=None):
        result = _update_metrics(qs=qs, replace_minute=replace_minute, **query)
        logger.debug('END update_metrics task')
        return result

def _update_metrics(qs=None, replace_minute=True, **query):
    """
    Test.objects.update_one(inc__embedded__number=1)
    
    Utiliser meme methode pour dec__metric__xxx quand doc supp ou modifié
    
    Vérifications:
        >>> models.Metric.objects(key_type=1).sum('metrics.total_size')
        144286581.0
        >>> models.MessageStore.objects.sum('size')
        144286581.0
        
    - Avec minute, pour 8468 MessageStore, 29936 Metric créés         
    - Sans minute, pour 8468 MessageStore, 19570 Metric créés         
    """
    
    start = time.time()
    
    qs = qs or models.MessageStore.objects(**query)

    #Exclude MessageStore already metric     
    qs = qs.filter(metric__ne=1, completed__ne=0)
    
    bulk_ids = []
    
    #TODO: pool gevent ?
    for doc in qs:
        update_metrics_one(doc, replace_minute=replace_minute)
        bulk_ids.append(doc.id) 
    
    end = time.time() - start
    
    logger.info("timed[%.3f]" % end)
    
    return models.MessageStore.objects(id__in=bulk_ids).update(metric=1)

def metrics_query(key_type=None,
                  is_group_key=True,
                  in_groups=None,
                  first_time=None, last_time=None,
                  date_year=True,                  
                  date_month=True,
                  date_day=True,                    
                  date_hour=False,
                  date_minute=False,
                  sort_desc=True, 
                  #limit=None,
                  #custom_query=None,
                  return_cursor=False):

    col = models.Metric._get_collection()

    query = {'$match': { }}
    
    #custom_query = {'internal_field': {'$eq': 1}}
    #if custom_query:
    #    query['$match'].update(custom_query)
    
    if key_type:
        query['$match']['key_type'] = {'$eq': key_type}
    
    if first_time or last_time:
        query['$match']['date'] = {}
    
    if first_time:
        query['$match']['date']['$gte'] = first_time

    if last_time:
        query['$match']['date']['$lte'] = last_time
        
    if in_groups:
        query['$match']['group_name'] = {'$in': in_groups}
        
    """
    >>> project = {'$project': { '_id': 0, 'key': 1, 'metrics': 1, 'date': {'y': { '$year': '$date' }, 'm': { '$month': '$date' }, 'd': { '$dayOfMonth': '$date' }}}}
    >>> group_by = {'$group': {'_id': {'year': '$date.y', 'month': '$date.m', 'day': '$date.d'}, 'mail_count': { '$sum': '$metrics.count' }}}
    >>> for m in models.Metric.objects(key_type=constants.METRIC_KEY_TYPE_GROUP).order_by('-date').aggregate(project, group_by): print m
    {u'_id': {u'year': 2015, u'day': 6, u'month': 4}, u'mail_count': 679}
    {u'_id': {u'year': 2015, u'day': 8, u'month': 4}, u'mail_count': 1}
    {u'_id': {u'year': 2015, u'day': 10, u'month': 4}, u'mail_count': 4563}
    {u'_id': {u'year': 2015, u'day': 11, u'month': 4}, u'mail_count': 11000}
    {u'_id': {u'year': 2015, u'day': 12, u'month': 4}, u'mail_count': 491}    
    """
        
    group_by = { 
        '$group': {
             '_id': {                   #l'ensemble devient la clé de regroupement
                 #'key':'$key',
                 #'year': '$date.y',
                 #'month': '$date.m',
                 #'day': '$date.d',
                 #'dateDifference': '$pdate.dateDifference',
             },
             #'new_date': "$date.yearMonthDay",
             'size_avg': { '$avg': '$metrics.total_size' }, 
             'size_sum': { '$sum': '$metrics.total_size' },
             'mail_count': { '$sum': '$metrics.count' },
             'mail_in': { '$sum': '$metrics.mail_in' },
             'mail_out': { '$sum': '$metrics.mail_out' },
             'clean': { '$sum': '$metrics.clean' },
             'spam': { '$sum': '$metrics.spam' },
             'virus': { '$sum': '$metrics.virus' },
             'banned': { '$sum': '$metrics.banned' },
             'unchecked': { '$sum': '$metrics.unchecked' },
             'bounce': { '$sum': '$metrics.bounce' },
             'files_count': { '$sum': '$metrics.files_count' },
        } 
    }
    
    if is_group_key:
        group_by['$group']['_id']['key'] = '$key'

    if date_year:
        group_by['$group']['_id']['year'] = '$pdate.y'
    
    if date_month:
        group_by['$group']['_id']['month'] = '$pdate.m'
    
    if date_day:
        group_by['$group']['_id']['day'] = '$pdate.d'

    if date_hour:
        group_by['$group']['_id']['hour'] = '$pdate.h'
    
    if date_minute:
        group_by['$group']['_id']['minute'] = '$pdate.mn'
        
    if len(group_by['$group']['_id']) == 0:
        group_by['$group']['_id'] = 'null'
        
    #print group_by['$group']['_id']
    
    project =  {  
        '$project': {
             '_id': 0,
             'group_name': 1,
             'key': 1,
             'key_type': 1,
             'metrics': 1,
             #'dateDifference': { '$subtract': [ last_time, "$date" ] },
             'pdate': {
                 'y': { '$year': '$date' },
                 'm': { '$month': '$date' },
                 'd': { '$dayOfMonth': '$date' }, 
                 'h': { '$hour': '$date' }, 
                 'mn': { '$minute': '$date' },
                 #mongo 3: 'yearMonthDay': { '$dateToString': { 'format': "%Y-%m-%d", 'date': "$date" } },
                 #'yearMonthDay': "$date"
              },
        } 
    }
    
    from bson.son import SON
    
    sort_by = { 
       #'$sort': { 
       #     '_id.year': -1 if sort_desc else 1, 
       #     '_id.month': -1 if sort_desc else 1, 
       #     '_id.day': -1 if sort_desc else 1, 
       # }  #-1 = desc, 1 = asc
       #'$sort': SON([('_id.year', -1 if sort_desc else 1)])
       #{"$sort": SON([("count", -1), ("_id", -1)])
       '$sort': SON([('_id.year', -1 if sort_desc else 1), 
                     ('_id.month', -1 if sort_desc else 1), 
                     ('_id.day', -1 if sort_desc else 1),
                     ('_id.hour', -1 if sort_desc else 1),
                     ('_id.minute', -1 if sort_desc else 1),
                     ])
              
    }
    pipeline = [
             query,
             project,
             group_by,
             sort_by
    ]
    #if limit:
    #    pipeline.append({'$limit': limit})
    #print "sort_by : ", sort_by
    
    result = col.aggregate(pipeline, cursor={})
    
    if return_cursor:
        return result
    
    return [r for r in result]

def metrics_top_convert(result, limit=10, field='mail_count'):
    metrics = {}
    
    for r in result:
        value = r.get(field)
        if value > 0:
            metrics[r['_id']['key']] = r.get(field)
    
    return sorted(metrics.items(), key=itemgetter(1), reverse=True)[:limit]

def metrics_top_country(limit=10, field='mail_count', **query):
    """
    > mail_count
    > size
    
    >>> metrics_top_country_by_year()
    [(u'US', 272),
     (u'CN', 41),
     (u'JP', 36),
     (u'KR', 27),
     (u'GB', 15),
     (u'DE', 14),
     (u'FR', 12),
     (u'CA', 12),
     (u'BR', 11),
     (u'NL', 9)] 
    """
    result= metrics_query(key_type=constants.METRIC_KEY_TYPE_COUNTRY, 
                         date_year=False, 
                         date_month=False,
                         date_day=False, **query)
    
    return metrics_top_convert(result, limit=limit, field=field)

