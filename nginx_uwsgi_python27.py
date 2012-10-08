# -----BEGIN WEBFACTION INSTALL SCRIPT-----
#!/usr/local/bin/python2.7
"""
Serve arbitrary WSGI web apps with nginx and uWSGI.

Expected structure:

app/
  wsgi.py - Required. Should contain your WSGI app.
  requirements.txt - Optional. a Pip requirements file.
  post-update - Optional. A shell script that is run after an update, to do things like DB migrations.

When you set up your deployment process, set it up to copy your app to the <appname>/app folder and call the update-app script.
"""

import xmlrpclib
import sys

NGINX_CONF = """
worker_processes  1;
pid               pid/nginx.pid;

error_log         ~/logs/user/error_APPNAME.log;

events {
  worker_connections  1024;
}

http {
  # Some sensible defaults.
  include               mime.types;
  default_type          application/octet-stream;
  keepalive_timeout     10;
  client_max_body_size  20m;
  sendfile              on;
  gzip                  on;

  # Directories
  client_body_temp_path tmp/client_body/  2 2;
  fastcgi_temp_path     tmp/fastcgi/;
  proxy_temp_path       tmp/proxy/;
  uwsgi_temp_path       tmp/uwsgi/;

  # Logging
  access_log            ~/logs/user/access_APPNAME.log  combined;

  # uWSGI upstream config
  upstream wsgi {
	# Distribute requests to servers based on client IP. This keeps load
	# balancing fair but consistent per-client. In this instance we're
	# only using one uWGSI worker anyway.
	ip_hash;
	server unix:sock/uwsgi.sock;
  }

  server {
	listen      PORT;
	charset     utf-8;

	location / {
	  uwsgi_pass  wsgi;
	  include     uwsgi_params;
	}
  }
}
"""

UWSGI_CONFIG = """
"""

UWSGI_VERSION = '1.3'
NGINX_VERSION = '1.3.6'

def create(account, app_name, autostart, extra_info, password, server, session_id, username):
	# create a custom app
	app = server.create_app(session_id, app_name, 'custom_app_with_port', False, '')
	
	install_steps = (
		# make directories
		'mkdir bin conf lib lib/python2.7 pid sock app tmp',
		
		# download
		'cd build',
		'curl -O https://projects.unbit.it/downloads/uwsgi-{}.tar.gz'.format(UWSGI_VERSION),
		'curl -O http://nginx.org/download/nginx-{}.tar.gz'.format(NGINX_VERSION),
		
		# install uwsgi
		'tar xf uwsgi-{}.tar.gz'.format(UWSGI_VERSION),
		'cd uwsgi-{}'.format(UWSGI_VERSION),
		'make',
		'mv uwsgi ../../bin',
		'cd ..',
		
		# install nginx
		'tar xf nginx-{}.tar.gz'.format(NGINX_VERSION),
		'cd nginx-{}'.format(NGINX_VERSION),
		'./configure',
		'make',
		'mv objs/nginx ../../bin',
		'cd ..',
		
		# install required conf files
		'cd ..',
		'cp build/nginx-{}/conf/mime.types conf/'.format(NGINX_VERSION),
		'cp build/uwsgi-{}/nginx/uwsgi_params conf/'.format(UWSGI_VERSION),
	)
	
	# run install steps
	server.system(session_id, '; '.join(install_steps))
	
	# install nginx.conf
	nginx_conf = NGINX_CONF.replace('APPNAME', app_name).replace('PORT', port)
	server.write_file(session_id, 'conf/nginx.conf', nginx_conf, 'w')
	
	# create database if required
	if 'postgres' in extra_info:
		db_name = db_user = '%s_%s' % (username, app_name)

def delete(account, app_name, autostart, extra_info, password, server, session_id, username):
	# Delete application and database.
	server.delete_app(session_id, app_name)
	try:
		server.delete_db(session_id, '%s_%s' % (username, app_name), 'postgres')
	except:
		pass

if __name__ == '__main__':
	action, username, password, machine, app_name, autostart, extra_info = sys.argv[1:]
	server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
	session_id, account = server.login(username, password, machine)
	func = locals()[action]
	func(account, app_name, autostart, extra_info, password, server, session_id, username)
# -----END WEBFACTION INSTALL SCRIPT-----