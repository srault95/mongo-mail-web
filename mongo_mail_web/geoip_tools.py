# -*- coding: utf-8 -*-

"""
http://dev.maxmind.com/geoip/legacy/geolite/
Country     Yes     Yes     MaxMind Country product page
    http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
    http://geolite.maxmind.com/download/geoip/database/GeoIPv6.dat.gz
City     Yes     Yes     MaxMind City product page
    http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
    http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.dat.gz
    
    CSV pour import dans DB:
        http://geolite.maxmind.com/download/geoip/database/GeoLiteCity_CSV/GeoLiteCity-latest.zip
        http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.csv.gz
"""
#TODO: Optimisations
"""
Create your GeoIP instance with appropriate access flag. 
    STANDARD reads data from disk when needed, 
    MEMORY_CACHE loads database into memory on instantiation
    MMAP_CACHE loads database into memory using mmap.
"""

#---Country:
"""
>>> gi = pygeoip.GeoIP('GeoIP.dat')
>>> gi.country_code_by_name('google.com')
'US'
>>> gi.country_code_by_addr('64.233.161.99')
'US'
>>> gi.country_name_by_addr('64.233.161.99')
'United States'

>>> gi = pygeoip.GeoIP('GeoIPv6.dat')
>>> gi.country_code_by_addr('2a00:1450:400f:802::1006')
'IE'
"""

#---City:
"""
TODO: A utiliser pour géolocalisation avec latitude/longitude


>>> gi = pygeoip.GeoIP('GeoIPCity.dat')
>>> gi.record_by_addr('64.233.161.99')
{
    'city': u'Mountain View',
    'region_code': u'CA',
    'area_code': 650,
    'time_zone': 'America/Los_Angeles',
    'dma_code': 807,
    'metro_code': 'San Francisco, CA',
    'country_code3': 'USA',
    'latitude': 37.41919999999999,
    'postal_code': u'94043',
    'longitude': -122.0574,
    'country_code': 'US',
    'country_name': 'United States',
    'continent': 'NA'
}
>>> gi.time_zone_by_addr('64.233.161.99')
'America/Los_Angeles'
"""

import os
import logging

from IPy import IP

import pygeoip 

logger = logging.getLogger(__name__)

geoip_country_v4 = None
geoip_country_v6 = None

DEFAULT_DB_COUNTRY_IPV4 = os.environ.get('GEOIP_COUNTRY_V4', 'GeoIP.dat')
DEFAULT_DB_COUNTRY_IPV6 = os.environ.get('GEOIP_COUNTRY_V6', 'GeoIPv6.dat')

DEFAULT_DB_CITY_IPV4 = os.environ.get('GEOIP_CITY_V4', 'GeoLiteCity.dat')
DEFAULT_DB_CITY_IPV6 = os.environ.get('GEOIP_CITY_V6', 'GeoLiteCityv6.dat')

try:
    from geoip_data import where_country_ipv4, where_country_ipv6
    HAVE_GEOIP_DATA = True
except ImportError:
    HAVE_GEOIP_DATA = False

def is_configured(ipv6=True):
    if not ipv6:
        return not geoip_country_v4 is None
    else:
        return not geoip_country_v4 is None and not geoip_country_v6 is None   

def is_public_address(address):
    try:
        return IP(address).iptype() == 'PUBLIC'
    except:
        return False
    
def is_v6_address(address):
    try:
        return IP(address).version() == 6
    except:
        return False



def check_country(ipaddr):
    """Check ip address - Release common for GeoIP (api C) and pygeoip
    
    >>> import os
    >>> from rs_common.tools import geoip_tools as geoip
    >>> os.path.exists(geoip.DEFAULT_DB_COUNTRY_IPV4)
    True
    >>> os.path.exists(geoip.DEFAULT_DB_COUNTRY_IPV6)
    True
    >>> geoip.configure_geoip()    
    >>> geoip.check_country('192.168.0.1')            
    Traceback (most recent call last):
        ...
    Exception: Not public address : 192.168.0.1
    >>> geoip.check_country('64.233.161.99')
    ('US', 'United States')
    
    #>>> geoip.configure_geoip(filepath_geoip_country_v4='/BADPATH/GeoIP.dat')
    #Traceback (most recent call last):
    #    ...
    #Exception: can't create GeoIP instance: [Errno 2] No such file or directory: '/BADPATH/GeoIP.dat'
    """
    
    try:            
        if not is_public_address(ipaddr):
            raise Exception("Not public address : %s" % ipaddr)
        
        if is_v6_address(ipaddr):
            
            if not geoip_country_v6:
                logger.error("Geoip country not configured for IPv6")
                raise Exception("Geoip country not configured for IPv6")
            
            country_code = geoip_country_v6.country_code_by_addr_v6(ipaddr)
            country_name = geoip_country_v6.country_name_by_name_v6(ipaddr)
        else:
            country_code = geoip_country_v4.country_code_by_addr(ipaddr)
            country_name = geoip_country_v4.country_name_by_addr(ipaddr)
        
        return country_code, country_name
    
    except Exception, err:
        logger.error(str(err))
        raise Exception(err)

    
def configure_geoip(filepath_geoip_country_v4=None, filepath_geoip_country_v6=None):
    """Method for configure checker GeoIP
    
    >>> import os
    >>> from rs_common_models import geoip_tools as geoip
    >>> os.path.exists(geoip.DEFAULT_DB_COUNTRY_IPV4)
    True
    >>> os.path.exists(geoip.DEFAULT_DB_COUNTRY_IPV6)
    True
    >>> geoip.configure_geoip(filepath_geoip_country_v4=geoip.DEFAULT_DB_COUNTRY_IPV4, filepath_geoip_country_v6=geoip.DEFAULT_DB_COUNTRY_IPV6)
    >>> geoip.geoip_country_v4 is None
    False
    >>> geoip.geoip_country_v6 is None
    False
    >>> geoip.geoip_country_v4.country_code_by_addr('64.233.161.99')            
    'US'
    """

    global geoip_country_v4
    global geoip_country_v6
    
    filepath_geoip_country_v4 = filepath_geoip_country_v4 or DEFAULT_DB_COUNTRY_IPV4
    filepath_geoip_country_v6 = filepath_geoip_country_v6 or DEFAULT_DB_COUNTRY_IPV6
    
    try:
        if filepath_geoip_country_v4 and os.path.exists(filepath_geoip_country_v4):
            geoip_country_v4 = pygeoip.GeoIP(filepath_geoip_country_v4, flags=pygeoip.MMAP_CACHE)

        if filepath_geoip_country_v6 and os.path.exists(filepath_geoip_country_v6): 
            geoip_country_v6 = pygeoip.GeoIP(filepath_geoip_country_v6, flags=pygeoip.MMAP_CACHE)
        
        if not geoip_country_v4 and HAVE_GEOIP_DATA:
             geoip_country_v4 = pygeoip.GeoIP(where_country_ipv4(), flags=pygeoip.MMAP_CACHE)

        if not geoip_country_v6 and HAVE_GEOIP_DATA:
             geoip_country_v6 = pygeoip.GeoIP(where_country_ipv6(), flags=pygeoip.MMAP_CACHE)
        
    except Exception, err:
        logger.error("can't create GeoIP instance: %s"  % err)
        raise Exception("can't create GeoIP instance: %s"  % err)


def update_datfiles(target_path=None):
    """ Télécharge ou met à jour les fichiers .dat de GeoIP
    
    TODO: utiliser un repo github geoip-data ? à mettre à jour automatiquement
    > si licence le permet ?
    
    >>> import tempfile, os
    >>> from rs_common.tools import geoip_tools as geoip
    >>> tmpdir = tempfile.gettempdir()
    >>> geoip.update_datfiles(tmpdir)
    >>> f = os.path.abspath(os.path.join(tmpdir, 'GeoIP.dat.gz'))
    >>> os.path.exists(f)
    True
    """
    
    """
    http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
    http://geolite.maxmind.com/download/geoip/database/GeoIPv6.dat.gz
    
    12Mo
    http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
    12Mo
    http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.dat.gz
    
    1. download
    2. décompresse tmp file
    3. supp et remplace ancien fichiers
    4. met à jour un fichier de status
    
    """
    
    import requests
    import gzip
    
    FILES = [
        dict(url='http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz', source='GeoIP.dat.gz', target='GeoIP.dat'),
        #dict(url='http://geolite.maxmind.com/download/geoip/database/GeoIPv6.dat.gz', source='GeoIPv6.dat.gz', target='GeoIPv6.dat'),
    ]
    
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        raise Exception("Not valid target path : %s" % target_path)
    
    for f in FILES:
        url = f['url']
        source = os.path.abspath(os.path.join(target_path, f['source']))
        target = os.path.abspath(os.path.join(target_path, f['target']))
    
        r = requests.get(url, stream=True)
        
        """
        #print "HEADERS : ", r.headers
        {'content-length': '428181', 'set-cookie': '__cfduid=d06615357da3dc7588ab627a58db7f8f81417754448; expires=Sat, 05-Dec-15 04:40:48 GMT; path=/; domain=.maxmind.com; HttpOnly', 'cf-cache-status': 'HIT', 'expires': 'Fri, 05 Dec 2014 08:40:48 GMT', 'vary': 'Accept-Encoding', 'server': 'cloudflare-nginx', 'last-modified': 'Tue, 02 Dec 2014 21:43:42 GMT', 'connection': 'keep-alive', 'cache-control': 'public, max-age=14400', 'date': 'Fri, 05 Dec 2014 04:40:48 GMT', 'cf-ray': '193d91589bce024a-CDG', 'content-type': 'application/octet-stream', 'accept-ranges': 'bytes'}        
        #return
        """
                
        if os.path.exists(source):
            os.remove(source)
            
        with open(source, 'wb') as fp:
            fp.write(r.raw.read())
            fp.flush()
            
            """
            FIXME: corruption du fichier
            
            for line in r.iter_lines(decode_unicode=False):
                if line:
                    fp.write(line)
                    fp.flush()
            
            fp.flush()
            """
        
        if os.path.exists(target):
            os.remove(target)

        #TODO: faire un target tmp et tester check avant remplacement
        #TODO: verrou !        
        with gzip.open(source, 'rb') as fp:
            with open(target, 'wb') as fp_target:
                fp_target.write(fp.read())
                
    

def _test():
    import doctest
    doctest.testmod()
    
if __name__ == "__main__":
    #python -m rs_common.tools.geoip_tools --test
    #python -m rs_common.tools.geoip_tools -v --test
    #TODO: ? nosetests rs_common.tools.geoip_tools 
    import sys
    import logging
    
    import rs_common
    #TODO: utiliser env
    GEOIP_DATA = os.path.abspath(os.path.join(os.path.dirname(rs_common.__file__), '..', 'geoip'))
    os.environ.setdefault('GEOIP_COUNTRY_V4', os.path.join(GEOIP_DATA, 'GeoIP.dat'))
    os.environ.setdefault('GEOIP_COUNTRY_V6', os.path.join(GEOIP_DATA, 'GeoIPv6.dat'))
    
    if '-v' in sys.argv: 
        logging.basicConfig(level=logging.DEBUG)
    
    if '--test' in sys.argv: 
        _test() 
        
    
