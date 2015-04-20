# -*- coding: utf-8 -*-

import logging

import gevent
from gevent.pool import Pool

from mongolock import MongoLockLocked

from . import models
from . import metrics
from . import constants

logger = logging.getLogger(__name__)

def completed_message_task(sleep=10.0, pool_size=10):
    
    pool = Pool(pool_size)
    
    while True:
        gevent.sleep(sleep)
                
        docs = models.MessageStore.objects(completed__ne=1)
        greenlets = []
        for doc in docs:
            greenlets.append(pool.spawn(doc._complete))

        if len(greenlets) > 0:
            pool.join()

def update_metrics_task(sleep=10.0):

    while True:
        gevent.sleep(sleep)
        try:
            metrics.update_metrics()
        except MongoLockLocked, err:
            logger.warning(str(err))
        except Exception, err:
            logger.error(str(err))


def demo_task(**kwargs):
    domains = [d.name for d in models.Domain.objects]
    mynetworks = [m.ip_address for m in models.Mynetwork.objects(address_type=constants.MYNETWORK_TYPE_IP)]
    
    from mm_tools.gevent_tasks import sent_fake_mail_task
    gevent.spawn(sent_fake_mail_task, domains=domains, mynetworks=mynetworks, **kwargs)
    
def run_all_tasks(is_demo=False, completed_sleep=10.0, completed_pool=10, update_metrics_sleep=10.0, demo_task_settings={}):
    gevent.spawn(completed_message_task, sleep=completed_sleep, pool_size=completed_pool)
    gevent.spawn(update_metrics_task, sleep=update_metrics_sleep)
    if is_demo:
        gevent.spawn(demo_task, **demo_task_settings)
        
    
    
        

