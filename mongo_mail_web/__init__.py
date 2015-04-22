
try:
    from gevent import monkey
    monkey.patch_all()
except:
    pass    

try:
    import pymongo
    if pymongo.version_tuple[0] < 3:
        PYMONGO2 = True
    else:
        PYMONGO2 = False
except ImportError:
    pass
