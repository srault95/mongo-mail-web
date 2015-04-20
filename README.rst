============================
Web UI for Mongo Mail Server
============================

|pypi downloads| |pypi dev_status| |pypi version| |pypi licence| |pypi py_versions|

**Demo:**

- URL: http://188.165.254.60:8083
- Login: admin@example.net
- Password: password

.. contents:: **Table of Contents**
    :depth: 1
    :backlinks: none

UI
==

Bootswatch themes
-----------------

.. image:: http://espace-groupware.com/docs/mongo-mail/img/mongo-mail-web-dashboards-mini.png
   :align: center

   
Messages Statistics
-------------------

.. image:: http://espace-groupware.com/docs/mongo-mail/img/dashboard-default-tb.png
   :align: center

   
Country Map
-----------

.. image:: http://espace-groupware.com/docs/mongo-mail/img/dashboard-country-tb.png
   :align: center


Multi Top Ten
-------------
   
.. image:: http://espace-groupware.com/docs/mongo-mail/img/dashboard-top-ten-tb.png
   :align: center

   
Messages Tables
---------------

.. image:: http://espace-groupware.com/docs/mongo-mail/img/message-table-tb.png
   :align: center

Messages Search
---------------

.. image:: http://espace-groupware.com/docs/mongo-mail/img/message-table-search-tb.png
   :align: center



Messages show
-------------
   
.. image:: http://espace-groupware.com/docs/mongo-mail/img/show-message-tb.png
   :align: center

   
Metrics tables
--------------

.. image:: http://espace-groupware.com/docs/mongo-mail/img/metrics-table-tb.png
   :align: center

   
Installation
============

Without Docker
--------------

**Required:**

- MongoDB Server
- Mongo Mail Server
- Python 2.7.6+ (< 3.x)
- python-gevent 1.0+
- recent setuptools and pip installer
- Nginx (optionnal)

**Installation:**

.. code:: bash

    $ pip install mongo-mail-web

    $ mongo-mail-web --help

With Docker
-----------

In progress...

See demonstration environment: `Mongo Mail Demo`_

Configuration With Environment
==============================

MMW_SETTINGS
------------

Module Setting 

Default: mongo_mail_web.settings.Prod

.. code:: bash

    # with command mode
    $ export MMW_SETTINGS=mongo_mail_web.settings.Prod
    
    # with docker environ
    $ docker run -e MMW_SETTINGS=mongo_mail_web.settings.Prod
    
    # with command arguments
    $ mongo-mail-web -c mongo_mail_web.settings.Prod <CMD>
    
MMW_MONGODB_URI
---------------

*Default*: mongodb://localhost/message

http://docs.mongodb.org/manual/reference/connection-string/

MMW_SUPERADMIN_EMAIL / MMW_SUPERADMIN_PASSWORD
----------------------------------------------

*Default*: admin@example.net / password
     
Configuration With local_settings
=================================

.. code:: python

    # local_settings.py in PYTHONPATH or current Path
    SECRET_KEY = "A1234"
        
.. code:: bash

    $ mongo-mail-web -c mongo_mail_web.settings.Custom <CMD>
   
   
TODO
====

- Tests
- Wizard configuration
- Websocket
- Outsourcing jobs to celery to share with Mongo Mail Server
- Specifics features for Filter mode, Turing Filter, Quarantine...
- Purge task
- PDF Exporting
- Mail Reporting
- Rest API

Contributing
============

To contribute to the project, fork it on GitHub and send a pull request, all contributions and suggestions are welcome.


.. _`Mongo Mail Server`: https://github.com/srault95/mongo-mail-server
.. _`Mongo Mail Web`: https://github.com/srault95/mongo-mail-web
.. _`Mongo Mail Demo`: https://github.com/srault95/mongo-mail-demo
.. _MongoDB: http://mongodb.org/
.. _Docker: https://www.docker.com/
.. _Ubuntu: http://www.ubuntu.com/
.. _Dockerfile: http://dockerfile.github.io/#/mongodb
.. _Python: http://www.python.org/
.. _Gevent: http://www.gevent.org/
.. _Postfix: http://www.postfix.org
.. _XFORWARD: http://www.postfix.org/XFORWARD_README.html
.. _MongoEngine: http://mongoengine.org/
.. _Flask-Admin: https://flask-admin.readthedocs.org/en/latest/
.. _Flask: http://flask.pocoo.org/ 
.. _Flask-Moment: https://github.com/miguelgrinberg/Flask-Moment
.. _Flask-Security: http://packages.python.org/Flask-Security/  
.. _Flanker: https://github.com/srault95/flanker/tarball/light_deps
.. _python-decouple: https://pypi.python.org/pypi/python-decouple/
.. _pygeoip: https://pypi.python.org/pypi/pygeoip
.. _Arrow: http://arrow.readthedocs.org/
.. _HighCharts: http://highcharts.com/
.. _`jQuery VectorMap`: http://jvectormap.com 

.. |pypi downloads| image:: https://pypip.in/download/mongo-mail-web/badge.svg
    :target: https://pypi.python.org/pypi/mongo-mail-web
    :alt: Number of PyPI downloads
    
.. |pypi version| image:: https://pypip.in/version/mongo-mail-web/badge.svg
    :target: https://pypi.python.org/pypi/mongo-mail-web
    :alt: Latest Version    

.. |pypi licence| image:: https://pypip.in/license/mongo-mail-web/badge.svg
    :target: https://pypi.python.org/pypi/mongo-mail-web
    :alt: License

.. |pypi py_versions| image:: https://pypip.in/py_versions/mongo-mail-web/badge.svg
    :target: https://pypi.python.org/pypi/mongo-mail-web
    :alt: Supported Python versions

.. |pypi dev_status| image:: https://pypip.in/status/mongo-mail-web/badge.svg
    :target: https://pypi.python.org/pypi/mongo-mail-web
    :alt: Development Status