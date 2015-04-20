# -*- coding: utf-8 -*-

import time
import sys
import random
import operator

import arrow
from dateutil.relativedelta import relativedelta

from mongo_mail_web import models
from mongo_mail_web import constants

"""
> tous les N docs:
    use model.Metric.objects.insert([], load_bulk=False)
    
last = arrow.utcnow().floor('day')
first = last.replace(years=-1)

first
<Arrow [2014-04-17T00:00:00+00:00]>
last
<Arrow [2015-04-17T00:00:00+00:00]>
    
arrow.Arrow.range('month', first, last)

from arrow import factory
myarrow = factory.ArrowFactory(demo.PerfArrow)
for month in myarrow.type.range('month', first, last): print month

for month in myarrow.type.range('month', first, last, limit=2): print month

> Pas de end, basé sur limit
for month in myarrow.type.range('month', first, limit=2): print month
2014-04-17T00:00:00+00:00
2014-05-17T00:00:00+00:00    
"""

class PerfArrow(arrow.Arrow):
    
    @classmethod
    def range(cls, frame, start, end=None, tz=None, limit=None):
        ''' Returns an array of :class:`Arrow <arrow.arrow.Arrow>` objects, representing
        an iteration of time between two inputs.

        :param frame: the timeframe.  Can be any ``datetime`` property (day, hour, minute...).
        :param start: A datetime expression, the start of the range.
        :param end: (optional) A datetime expression, the end of the range.
        :param tz: (optional) A timezone expression.  Defaults to UTC.
        :param limit: (optional) A maximum number of tuples to return.

        **NOTE**: the **end** or **limit** must be provided.  Call with **end** alone to
        return the entire range, with **limit** alone to return a maximum # of results from the
        start, and with both to cap a range at a maximum # of results.

        Recognized datetime expressions:

            - An :class:`Arrow <arrow.arrow.Arrow>` object.
            - A ``datetime`` object.

        Recognized timezone expressions:

            - A ``tzinfo`` object.
            - A ``str`` describing a timezone, similar to 'US/Pacific', or 'Europe/Berlin'.
            - A ``str`` in ISO-8601 style, as in '+07:00'.
            - A ``str``, one of the following:  'local', 'utc', 'UTC'.

        Usage:

            >>> start = datetime(2013, 5, 5, 12, 30)
            >>> end = datetime(2013, 5, 5, 17, 15)
            >>> for r in arrow.Arrow.range('hour', start, end):
            ...     print repr(r)
            ...
            <Arrow [2013-05-05T12:30:00+00:00]>
            <Arrow [2013-05-05T13:30:00+00:00]>
            <Arrow [2013-05-05T14:30:00+00:00]>
            <Arrow [2013-05-05T15:30:00+00:00]>
            <Arrow [2013-05-05T16:30:00+00:00]>

        '''

        frame_relative = cls._get_frames(frame)[1]
        tzinfo = cls._get_tzinfo(start.tzinfo if tz is None else tz)

        start = cls._get_datetime(start).replace(tzinfo=tzinfo)
        end, limit = cls._get_iteration_params(end, limit)
        end = cls._get_datetime(end).replace(tzinfo=tzinfo)

        current = cls.fromdatetime(start)
        #results = []
        count = 0

        while current <= end:
            #results.append(current)
            count += 1
            if count > limit:
                break
            
            yield current

            values = [getattr(current, f) for f in cls._ATTRS]
            current = cls(*values, tzinfo=tzinfo) + relativedelta(**{frame_relative: 1})

        #return results

def create_fixtures(batch=100):
    """
    1 an - 1 key_type - 8761 docs - 10 secs
    
    TODO: utiliser un formulaire ?
    
    """
    from arrow import factory
    
    start = time.time()
    
    models.Metric.objects(internal_field=1).delete()
    
    last = arrow.utcnow().floor('day')
    #first = last.replace(months=-1)    
    first = last.replace(years=-1)
    docs = []    
    myarrow = factory.ArrowFactory(PerfArrow)

    current = models.Metric.objects(internal_field=1).count()
    
    for date in myarrow.type.range('hour', first, last): 

        count = random.randint(1000, 10000)
        mail_in = random.randint(700, count)
        mail_out = count - mail_in
        files_count = random.randint(0, 10)
        total_size = random.randint(10, 1000000)
        
        clean = random.randint(500, 8000)
        spam = random.randint(clean, mail_in) # 500 -> 9000

        #spam = long(round(mail_in * random.randint(4, 6)*0.1)) # de 40% A 60%
        virus = long(round(mail_in * random.randint(1, 3)*0.1)) #10% A 30%
        banned = long(round(mail_in * random.randint(1, 2)*0.1)) #10% A 20%
        unchecked = long(round(mail_in * (random.randint(1, 2)*0.1)/2)) #10% A 20%
        bounce = long(round(count * random.randint(2, 3)*0.1)) #20% A 30%

        docs.append(models.Metric(internal_field=1,
                            date=date.datetime,
                            group_name=constants.GROUP_DEFAULT,
                            key=constants.GROUP_DEFAULT,
                            key_type=constants.METRIC_KEY_TYPE_GROUP,
                            metrics=models.MetricKeys(
                                        count=count,
                                        mail_in=mail_in,
                                        mail_out=mail_out,
                                        total_size=total_size,
                                        files_count=files_count,
                                        spam=spam,
                                        virus=virus,
                                        banned=banned,
                                        unchecked=unchecked,
                                        bounce=bounce
                                    )
                            ))
        
        if len(docs) > batch:
            models.Metric.objects.insert(docs, load_bulk=False)
            docs = []
    
    if len(docs) > 0:
        models.Metric.objects.insert(docs, load_bulk=False)
    
    end = time.time() - start
    print "CREATED[%s] - TIME[%.3f]" % (models.Metric.objects(internal_field=1).count() - current, end)
    