#!/usr/local/bin/python2.7
# -----BEGIN WEBFACTION INSTALL SCRIPT-----
#!/usr/local/bin/python2.7
"""
Sets up a Sentry installation.

After installing, you may wish to edit sentry.conf.py to change the URL prefix and gunicorn worker count.

You will also want to create a superuser by running this command: `bin/sentry --config=sentry.conf.py createsuperuser`, then `bin/sentry --config=sentry.conf.py repair --owner=<username>`.

Things that don't work: languages other than English, running Sentry on a subdirectory

Requires: supervisord, pip
"""

import xmlrpclib
import sys
import string 
import random

_old_stderr = sys.stderr
sys.stderr = sys.stdout

SENTRY_CONF = """
import os.path

CONF_ROOT = os.path.dirname(__file__)

DATABASES = {{
	'default': {{
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': '{db_name}',
		'USER': '{db_name}',
		'PASSWORD': '{db_pass}',
		'HOST': '',
		'PORT': '',
	}}
}}

# You should configure the absolute URI to Sentry. It will attempt to guess it if you don't
# but proxies may interfere with this.
# No trailing slash!
# SENTRY_URL_PREFIX = 'http://{app_name}.{username}.webfactional.com'

# SENTRY_KEY is a unique randomly generated secret key for your server, and it
# acts as a signing token
SENTRY_KEY = '{secret}'

SENTRY_PUBLIC = False

SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = {port}
SENTRY_WEB_OPTIONS = {{
	'workers': 2,  # the number of gunicorn workers
}}

# We're assuming you don't want to run a public Sentry installation.
SOCIAL_AUTH_CREATE_USERS = False

# This seems to be required for some reason, but it means that languages other than English can't be used.
# If you know a way around this, please file an issue or a pull request!
from sentry.conf.server import *
USE_I18N = False
USE_L10N = False
"""

SUPERVISOR_CONF = """
[program:app-{app_name}]
directory={app_dir}
command={sentry_bin} --config=sentry.conf.py start http
autostart=true
autorestart=true
redirect_stderr=true
"""

def generate_password(len):
	return ''.join(random.choice(string.ascii_letters + string.digits) for x in xrange(len))

def create(account, app_name, autostart, extra_info, password, server, session_id, username):
	app_dir = "/home/{}/webapps/{}".format(username, app_name)
	sentry_bin = app_dir + "/bin/sentry"
	pip_bin = "/home/{}/bin/pip-2.7".format(username)
	
	# create base app
	app = server.create_app(session_id, app_name, 'custom_app_with_port', False, '')
	port = app['port']
	
	# install sentry
	server.system(session_id, '{pip_bin} install -U --install-option="--install-scripts={app_dir}/bin" --install-option="--install-lib={app_dir}/lib/python2.7" sentry'.format(**locals()))

	# create database
	db_name = "{}_{}".format(username, app_name)
	db_pass = generate_password(20)
	server.create_db(session_id, db_name, 'postgresql', db_pass)
	
	# generate a secret
	secret = generate_password(56)
	
	# write config
	server.write_file(session_id, 'sentry.conf.py', SENTRY_CONF.format(**locals()), 'w')
	server.write_file(session_id, 'supervisord.conf', SUPERVISOR_CONF.format(**locals()), 'w')
	server.system(session_id, 'ln -s {}/supervisord.conf $HOME/supervisor/app_{}.conf'.format(app_dir, app_name))

	
	# build db
	# sometimes this causes a RuntimeWarning that may or may not be fatal
	try:
		server.system(session_id, '{} --config=sentry.conf.py upgrade --noinput'.format(sentry_bin))
	except xmlrpclib.Fault as f:
		server.write_file(session_id, 'install_error.log', 'Code {}\n{}'.format(f.faultCode, f.faultString))
	
	# start server
	server.system(session_id, '$HOME/bin/supervisorctl update')

	print app['id']

def delete(account, app_name, autostart, extra_info, password, server, session_id, username):
	# Delete application and database.
	try:
		server.system(session_id, 'unlink $HOME/supervisor/app_{}.conf'.format(app_name))
		server.system(session_id, '$HOME/bin/supervisorctl update')
	except:
		pass

	server.delete_app(session_id, app_name)

	try:
		server.delete_db(session_id, '%s_%s' % (username, app_name), 'postgresql')
	except:
		pass

if __name__ == '__main__':
	try:
		action, username, password, machine, app_name, autostart, extra_info = sys.argv[1:]
		server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
		session_id, account = server.login(username, password, machine)
		func = locals()[action]
		func(account, app_name, autostart, extra_info, password, server, session_id, username)
	except Exception as e:
		# try to delete the app
		try:
			delete(account, app_name, autostart, extra_info, password, server, session_id, username)
		except:
			pass
		# print the exception
		from traceback import print_exc
		print_exc(sys.stdout)
# -----END WEBFACTION INSTALL SCRIPT-----