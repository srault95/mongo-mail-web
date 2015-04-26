# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.rst") as fp:
    long_description = fp.read()
    
setup(
    name='mongo-mail-web',
    version='0.1.2',
    description='Web UI for Mongo Mail Server',
    long_description=long_description,
    author='Stéphane RAULT',
    author_email='stephane.rault@radicalspam.org',
    url='https://github.com/radical-software/mongo-mail-web',
    zip_safe=False,
    #platforms=[],    
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Framework :: Flask',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Communications :: Email',
        'Topic :: Communications :: Email :: Filters',
        'Natural Language :: English',
        'Natural Language :: French'         
    ],     
    include_package_data=True,
    packages=find_packages(),
    install_requires = [
        'python-dateutil',
        'arrow',
        'gevent>=1.0',
        'IPy',
        'python-decouple',
        'pymongo>=2.8,<3.0',
        'mongoengine>=0.9.0',
        'flask-mongoengine',
        'mongolock>=1.3.3',
        'flanker',
        'Flask-Script',
        'Flask-Login<0.3.0',
        'Flask-Security',
        'Flask-Moment',
        'Flask-BabelEx',
        'Flask-Admin>=1.1.0',
        'geoip-data',
        'pygeoip',
        'Flask-DebugToolbar',
        'Flask-CuddlyRest'
    ],
    dependency_links=[
      'https://github.com/MongoEngine/flask-mongoengine/tarball/master/#egg=flask-mongoengine-0.7.1',
      'https://github.com/srault95/flanker/tarball/light_deps/#egg=flanker-0.4.27',
      'https://github.com/srault95/geoip-data/tarball/master/#egg=geoip-data-0.1.1',
      'https://github.com/wuurrd/Flask-CuddlyRest.git#egg=Flask-CuddlyRest-0.1.14'
    ],      
    test_suite='nose.collector',
    tests_require=[
      'nose',
    ],
    entry_points={
        'console_scripts': [
            'mongo-mail-web = mongo_mail_web.manager:main',
        ],
    },
)
