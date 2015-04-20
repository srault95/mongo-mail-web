# -*- coding: utf-8 -*-

"""
@see: http://graphite.readthedocs.org/en/latest/render_api.html

RELATIVE_TIME:

    Abbreviation  Unit
    s             Seconds
    min           Minutes
    h             Hours
    d             Days
    w             Weeks
    mon           30 Days (month)
    y             365 Days (year)

ABSOLUTE_TIME is in the format HH:MM_YYMMDD, YYYYMMDD, MM/DD/YY:

    HH     Hours, in 24h clock format. Times before 12PM must include leading zeroes.
    MM     Minutes
    YYYY   4 Digit Year.
    MM     Numeric month representation with leading zero
    DD     Day of month with leading zero

"""

__all__ = [
    'period_request',
]

import datetime
from dateutil import parser
import pytz

from .graphite_attime import parseATTime

_ = lambda s:s

#---PERIOD - raccourcis pour range date format graphite

"""

    from        : DEBUT
    until       : FIN

    &from=-RELATIVE_TIME
    &from=ABSOLUTE_TIME

    Abbreviation     Unit
    s     Seconds
    min     Minutes
    h     Hours
    d     Days
    w     Weeks
    mon     30 Days (month)
    y     365 Days (year)

"""

"""
{"order_sort": 0, "host_name": null, "date_receive": "2012-08-28T21:35:10+00:00", "host_ip": "195.234.90.119"}    
"""

#PERIOD_TODAY = """{"from": "today"}"""
PERIOD_TODAY = {'from': 'today'}

# Hier à 00:00:00 A now
PERIOD_YESTERDAY = {'from': 'yesterday'}

PERIOD_LAST_24_HOURS = {'from': '-24h'}

# Last week - today - 1 semaine - même heure que now
PERIOD_LAST_WEEK = {'from': '-1w'}

PERIOD_LAST_YEAR = {'from': '-1y'}

PERIOD_LAST_2_YEAR = {'from': '-2y'}

PERIOD_LAST_MONTH = {'from': '-1mon'}

PERIOD_LAST_MONDAY = {'from': 'monday'}

# Même jour qu'aujourd'hui, il y a 1 semaine
PERIOD_SAME_DAY_LAST_WEEK = {'from': '-8d', 'until': '-7d'}


PERIOD_DICT = {
    'today': PERIOD_TODAY,
    'yesterday': PERIOD_YESTERDAY,
    'last-24-hours': PERIOD_LAST_24_HOURS,
    'last-week': PERIOD_LAST_WEEK,
    'last-month': PERIOD_LAST_MONTH,
    'last-year': PERIOD_LAST_YEAR,
    'last-2-year': PERIOD_LAST_2_YEAR,
    'last-monday': PERIOD_LAST_MONDAY,
    'same-day-last-week': PERIOD_SAME_DAY_LAST_WEEK,
}




"""
- dashboard: menu pour choix période d'affichage de toutes les stats du dashboard: today, yesterday, last week, last month, ..
"""


def smart_date(value):
    """Return range first/last datetime
    
    Usage:
    
    this-year:     du 01/01/YYYY au 31/12/YYYY ou now
    this-month:    du 01/MM/YYYY au ??/MM/YYYY ou now ?
    today ou this-day: 
    yesterday
    this-week
    
    last-year
    last-month
    last-week
    last-day
    
    date = smart_date('today')
    date = smart_date('today').date()
    date = smart_date('2013-01-01').date() #format dateutil.parse
    
    TODO: utiliser constants pour les mot clés !
        
    """

    if value == 'today':
        # Aujourd'hui
        return datetime.datetime.now()
    
    elif value == 'yesterday':
        # Hier
        """
        FIXME: renvoit -24 de l'heure en cours !!!
        
        TODO: Mettre datetime.datetime.now() à 0h00
        """
        return datetime.datetime.now() - datetime.timedelta(days=1)

    elif value == 'last_seven_days':
        # 7 derniers jours
        return datetime.datetime.now() - datetime.timedelta(days=7)
    
    elif value == 'tomorrow':
        # Demain ?
        return datetime.datetime.now() + datetime.timedelta(days=1)
    
    elif value == 'year_ago':
        # 1 an avant aujourd'hui
        return datetime.datetime.now() - datetime.timedelta(days=365)
    
    elif value == 'start_of_month':
        # Début du mois en cours
        today = datetime.datetime.today()
        return datetime.datetime(today.year, today.month, 1)
    
    elif value == 'start_of_year':
        # Début de l'année en cours
        today = datetime.datetime.today()
        return datetime.datetime(today.year, 1, 1)
    
    else:
        # Parse la date au format text
        return parser.parse(value, dayfirst=True)




def period_request(queryParams={}, tz=None, default_timezone='UTC'):
    u"""Renvoi une date de début et une date de fin pour la période demandé

    >>> from flask_helpers import metric_utils
    >>> metric_utils.period_request(metric_utils.PERIOD_TODAY)
    {'endTime': datetime.datetime(2015, 3, 10, 16, 57, 32, 911000, tzinfo=<UTC>),
    'startTime': datetime.datetime(2015, 3, 10, 0, 0, 0, 911000, tzinfo=<UTC>),
     'tzinfo': <UTC>}
     
    >>> from rs_flasktools.metric_constants import PERIOD_YESTERDAY
    >>> from rs_flasktools.metric_utils import period_request
    >>> queryParams = PERIOD_YESTERDAY    
    >>> requestOptions = period_request(queryParams)
    
    #>>> requestOptions['startTime']
    #>>> requestOptions['endTime']
    #>>> requestOptions['tzinfo']
    
    Optionnel:
    >>> queryParams = PERIOD_YESTERDAY
    >>> queryParams['tz'] = 'Europe/Paris'
        
    """
    
    requestOptions = {}
    
    tzinfo = tz or pytz.timezone(default_timezone)
    #if 'tz' in queryParams:
    #  try:
    #    tzinfo = pytz.timezone(queryParams['tz'])
    #  except pytz.UnknownTimeZoneError:
    #    pass
    requestOptions['tzinfo'] = tzinfo
    
    if 'until' in queryParams:
      untilTime = parseATTime(queryParams['until'], tzinfo=tzinfo)
    else:
      untilTime = parseATTime('now', tzinfo=tzinfo)
    
    if 'from' in queryParams:
      fromTime = parseATTime(queryParams['from'], tzinfo=tzinfo)
    else:
      fromTime = parseATTime('-1d', tzinfo=tzinfo)
    
    startTime = min(fromTime, untilTime)
    endTime = max(fromTime, untilTime)
    
    assert startTime != endTime, "Invalid empty time range"

    requestOptions['startTime'] = startTime
    requestOptions['endTime'] = endTime
    
    return requestOptions

def today():
    """
    usage:
    from metric_utils import today
    time_start, time_end = today()
    
    Return:
    (datetime.datetime(2014, 5, 26, 0, 0, 0, 311000, tzinfo=<DstTzInfo 'Europe/Paris' CEST+2:00:00 DST>),
     datetime.datetime(2014, 5, 26, 6, 30, 17, 311000, tzinfo=<DstTzInfo 'Europe/Paris' CEST+2:00:00 DST>))
     
     .filter(sys_receive__gte=time_start, sys_receive__lte=time_end)    
    """
    requestOptions = period_request(PERIOD_TODAY)
    return (requestOptions['startTime'], requestOptions['endTime'])

def yesterday():
    """
    ATTENTION, renvoi time en cours - 24 H !!!
    """
    requestOptions = period_request(PERIOD_YESTERDAY)
    return (requestOptions['startTime'], requestOptions['endTime'])
     
    

def test1():
    format = "%d-%m-%Y - %H:%M:%S - %Z"
    
    tests = PERIOD_CHOICES

    """
    tests.append( PERIOD_TODAY )
    tests.append( PERIOD_YESTERDAY )
    #same_day_last_week - Même jour qu'aujourd'hui, il y a 1 semaine
    tests.append( PERIOD_SAME_DAY_LAST_WEEK )    
    
    #t2 = {'from': 'noon+yesterday'} #https://github.com/graphite-project/graphite-web/issues/263
    #t3 = {'from': '6pm+today'}        #https://github.com/graphite-project/graphite-web/issues/263
    
    #Jour de cette semaine - monday=lundi - commence le lundi 00:00:00  
    tests.append( PERIOD_LAST_MONDAY )
    
    #Last week - today - 1 semaine - même heure que now
    tests.append( PERIOD_LAST_WEEK )
    """

    
    for queryParams, title in tests:
        # print "queryParams : ", queryParams     
        requestOptions = period_request(queryParams)
        """
        TODO: compter nombre de jour
        """
        count = requestOptions['endTime'] - requestOptions['startTime']
        day = (60 * 60) * 24        
        # count = ((count.total_seconds() / 60) / 60) / 24
        count = round(count.total_seconds() / 86400, 0)
        # print "count : ", count.total_seconds(), count.seconds
        # total_seconds
        # Equivalent to (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 
        
        print "title[%s] - from[%s] - until[%s] - startTime[%s] - endTime[%s] - %s JOURS" % (title,
                                                                                  queryParams.get('from', 'NULL'),
                                                                                  queryParams.get('until', 'NULL'),
                                                                                  requestOptions['startTime'].strftime(format),
                                                                                  requestOptions['endTime'].strftime(format),
                                                                                  count)
    """
    title[Aujourd'hui] - from[today] - until[NULL] - startTime[23-10-2013 - 00:00:00 - CEST] - endTime[23-10-2013 - 11:54:37 - CEST] - 0.0 JOURS

    title[Depuis hier] - from[yesterday] - until[NULL] - startTime[22-10-2013 - 00:00:00 - CEST] - endTime[23-10-2013 - 11:54:37 - CEST] - 1.0 JOURS

    title[Depuis 1 semaine] - from[-1w] - until[NULL] - startTime[16-10-2013 - 11:54:37 - CEST] - endTime[23-10-2013 - 11:54:37 - CEST] - 7.0 JOURS

    title[Depuis 1 mois] - from[-1mon] - until[NULL] - startTime[23-09-2013 - 11:54:37 - CEST] - endTime[23-10-2013 - 11:54:37 - CEST] - 30.0 JOURS

    title[Depuis 1 an] - from[-1y] - until[NULL] - startTime[23-10-2012 - 11:54:37 - CEST] - endTime[23-10-2013 - 11:54:37 - CEST] - 365.0 JOURS

    title[Dernier Lundi] - from[monday] - until[NULL] - startTime[21-10-2013 - 00:00:00 - CEST] - endTime[23-10-2013 - 11:54:37 - CEST] - 2.0 JOURS

    title[Même jour qu'aujourd'hui, il y a une semaine] - from[-8d] - until[-7d] - startTime[15-10-2013 - 11:54:37 - CEST] - endTime[16-10-2013 - 11:54:37 - CEST] - 1.0 JOURS    
    """
    
"""
Graphite:

&from=04:00_20110501&until=16:00_20110501
(shows 4AM-4PM on May 1st, 2011)

&from=20091201&until=20091231        Tous le mois de décembre 2009
(shows December 2009)

&from=noon+yesterday
(shows data since 12:00pm on the previous day)

&from=6pm+today
(shows data since 6:00pm on the same day)

&from=january+1
(shows data since the beginning of the current year)

&from=monday
(show data since the previous monday)
"""
    
      
if __name__ == "__main__":
    # python -m rs_flasktools.metric_utils
    test1()
