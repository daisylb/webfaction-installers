#!/usr/local/bin/python2.7
# -----BEGIN WEBFACTION INSTALL SCRIPT-----
#!/usr/local/bin/python2.7
"""
Sets up a Sentry installation.

After installing, will need to edit the created sentry.conf.py and follow the instructions there.

Things that don't work: languages other than English, running Sentry on a subdirectory

Requires: supervisord, pip
"""
from wfinstaller import CustomAppOnPortInstaller

import string 
import random

SENTRY_CONF = """
import os.path

##########################################################################
# You will need to edit the following lines for Sentry to work properly. #
##########################################################################

# This is the URL that Sentry is bound to.
# By default it will try to guess it, but it will almost certainly guess wrong due to WF's reverse proxy.
# It should NOT have a trailing slash.

# SENTRY_URL_PREFIX = 'http://{self.args.app_name}.{self.args.username}.webfactional.com'

# The installer creates a Sentry mailbox (named the same as the app) for you.
# You will need to attatch that mailbox to an email address, and then change the following line appropriately.

SERVER_EMAIL = '{self.args.app_name}@{self.args.username}.webfactional.com'

# Once you're done, run these commands:
# {sentry_bin} --config=sentry.conf.py upgrade
# supervisorctl start app-{self.args.app_name}

#######
# End #
#######

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

# SENTRY_KEY is a unique randomly generated secret key for your server, and it
# acts as a signing token
SENTRY_KEY = '{secret}'

SENTRY_PUBLIC = False

SENTRY_WEB_HOST = '0.0.0.0'
SENTRY_WEB_PORT = {self.port}
SENTRY_WEB_OPTIONS = {{
	'workers': 2,  # the number of gunicorn workers
}}

EMAIL_HOST = 'smtp.webfaction.com'
EMAIL_HOST_USER = '{db_name}'
EMAIL_HOST_PASSWORD = '{mail_pass}'
DEFAULT_FROM_EMAIL = SERVER_EMAIL

# We're assuming you don't want to run a public Sentry installation.
SOCIAL_AUTH_CREATE_USERS = False

# This seems to be required for some reason, but it means that languages other than English can't be used.
# If you know a way around this, please file an issue or a pull request!
from sentry.conf.server import *
USE_I18N = False
USE_L10N = False
"""

SUPERVISOR_CONF = """
[program:app-{self.args.app_name}]
directory={app_dir}
command={sentry_bin} --config=sentry.conf.py start http
autostart=true
autorestart=true
redirect_stderr=true
"""

def generate_password(len):
	return ''.join(random.choice(string.ascii_letters + string.digits) for x in xrange(len))

class SentryInstaller (CustomAppOnPortInstaller):
	def create(self):
		app_dir = "/home/{}/webapps/{}".format(self.args.username, self.args.app_name)
		sentry_bin = app_dir + "/bin/sentry"
		pip_bin = "/home/{}/bin/pip-2.7".format(self.args.username)
		
		# install sentry
		self.api.system('{pip_bin} install -U --install-option="--install-scripts={app_dir}/bin" --install-option="--install-lib={app_dir}/lib/python2.7" sentry'.format(**locals()))
	
		# create database
		db_name = "{}_{}".format(self.args.username, self.args.app_name)
		db_pass = generate_password(30)
		self.api.create_db(db_name, 'postgresql', db_pass)
		
		# create mailbox
		mail_pass = generate_password(30)
		self.api.create_mailbox(db_name, True, True)
		self.api.change_mailbox_password(db_name, mail_pass)
		
		# generate a secret
		secret = generate_password(56)
		
		# write config
		self.api.write_file('sentry.conf.py', SENTRY_CONF.format(**locals()), 'w')
		self.api.write_file('supervisord.conf', SUPERVISOR_CONF.format(**locals()), 'w')
		self.api.system('ln -s {}/supervisord.conf $HOME/supervisor/app_{}.conf'.format(app_dir, self.args.app_name))
	
		
		# build db
		# sometimes this causes a RuntimeWarning that may or may not be fatal
		#try:
		#	self.api.system('{} --config=sentry.conf.py upgrade --noinput'.format(sentry_bin))
		#except xmlrpclib.Fault as f:
		#	self.api.write_file('install_error.log', 'Code {}\n{}'.format(f.faultCode, f.faultString))
		
		# start server
		self.api.system('$HOME/bin/supervisorctl update')

	def delete(self):
		# Delete the supervisor config file.
		try:
			self.api.system('unlink $HOME/supervisor/app_{}.conf'.format(app_name))
			self.api.system('$HOME/bin/supervisorctl update')
		except:
			pass
			
		db_name = '{}_{}'.format(self.args.username, self.args.app_name)
		
		try:
			self.api.delete_db(db_name, 'postgresql')
			self.api.delete_db_user(db_name, 'postgresql')
		except:
			pass
		
		try:
			self.api.delete_mailbox(db_name)
		except:
			pass

if __name__ == '__main__':
	if __name__ == '__main__':
		import sys
		SentryInstaller().run(*sys.argv[1:])
# -----END WEBFACTION INSTALL SCRIPT-----