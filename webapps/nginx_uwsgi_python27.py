#!/usr/local/bin/python2.7
# -----BEGIN WEBFACTION INSTALL SCRIPT-----
#!/usr/local/bin/python2.7
"""
Serve arbitrary WSGI web apps with nginx and uWSGI.

Expected structure:

app/
  wsgi.py - Required. Should contain your WSGI app callable as `application`.
  requirements.txt - Optional. a Pip requirements file.
  update.sh - Optional. A shell script that is run after an update but before the server is reloaded. Can be used to deal with things like migrations.

When you set up your deployment process, set it up to copy your app to the <appname>/app folder and call the update-app script.

Requires: pip, supervisor
"""

import xmlrpclib
import sys

_old_stderr = sys.stderr
sys.stderr = sys.stdout

NGINX_CONF = """
worker_processes  1;
pid               DIR/pid/nginx.pid;

error_log         HOME/logs/user/error_APPNAME.log;

# Don't daemonize, as nginx is managed by supervisord
daemon           off;

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
  client_body_temp_path DIR/tmp/client_body/  2 2;
  fastcgi_temp_path     DIR/tmp/fastcgi/;
  proxy_temp_path       DIR/tmp/proxy/;
  uwsgi_temp_path       DIR/tmp/uwsgi/;

  # Logging
  access_log            HOME/logs/user/access_APPNAME.log  combined;

  # uWSGI upstream config
  upstream wsgi {
    # Distribute requests to servers based on client IP. This keeps load
    # balancing fair but consistent per-client. In this instance we're
    # only using one uWGSI worker anyway.
    ip_hash;
    server unix:DIR/sock/uwsgi.sock;
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

# aside: there is a better uwsgi.ini for Django at this url: http://projects.unbit.it/uwsgi/wiki/Example

UWSGI_INI = """
[uwsgi]
binary-path = DIR/bin/uwsgi
logto = HOME/logs/user/error_APPNAME_uwsgi.log

# nginx communication
socket = DIR/sock/uwsgi.sock
file-serve-mode = x-accel-redirect

# workers
workers = 2
pidfile = DIR/pid/uwsgi.pid
reload-on-rss = 48

# wsgi stuff
chdir = DIR/app/
module = wsgi:application
"""

SUPERVISOR_CONFIG = """
[group:app_APPNAME]
programs=app_APPNAME_uwsgi,app_APPNAME_nginx

[program:app_APPNAME_uwsgi]
command=DIR/bin/uwsgi --ini DIR/conf/uwsgi.ini
priority=1
autorestart=true
; these two are to stop uwsgi zombies
stopsignal=QUIT
stopasgroup=true

[program:app_APPNAME_nginx]
command=DIR/bin/nginx -c DIR/conf/nginx.conf
priority=2
autorestart=true
"""

RELOAD_APP = """
#!/bin/bash
set -e
if test -f DIR/app/requirements.txt; then
    pip-2.7 install --install-option="--install-scripts=DIR/bin" --install-option="--install-lib=DIR/lib/python2.7" -r DIR/app/requirements.txt
fi
if test -f DIR/app/update.sh; then
    (cd DIR/app && bash update.sh)
fi
supervisorctl restart app_APPNAME:*
"""

SAMPLE_APP = """
import sys

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield 'Hello World!\\\\n' + sys.version + '\\\\n'
"""

UWSGI_VERSION = '1.3'
NGINX_VERSION = '1.3.6'

def create(account, app_name, autostart, extra_info, password, server, session_id, username):
    # create a custom app
    # returns a dict containing name, id, machine, autostart, type, port, extra_info
    app = server.create_app(session_id, app_name, 'custom_app_with_port', False, '')
    app_dir = "/home/{}/webapps/{}".format(username, app_name)
    
    install_steps = (
        # make directories
        'mkdir build bin conf lib lib/python2.7 pid sock app tmp',
        
        # download
        'cd build',
        'mkdir -p ~/.dlcache',
        'if test ! -f ~/.dlcache/uwsgi-{}.tar.gz'.format(UWSGI_VERSION),
        'then curl -sSo ~/.dlcache/uwsgi-{v}.tar.gz https://projects.unbit.it/downloads/uwsgi-{v}.tar.gz'.format(v=UWSGI_VERSION),
        'fi',
        'cp ~/.dlcache/uwsgi-{}.tar.gz .'.format(UWSGI_VERSION),
        
        'if test ! -f ~/.dlcache/nginx-{}.tar.gz'.format(UWSGI_VERSION),
        'then curl -sSo ~/.dlcache/nginx-{v}.tar.gz http://nginx.org/download/nginx-{v}.tar.gz'.format(v=NGINX_VERSION),
        'fi',
        'cp ~/.dlcache/nginx-{}.tar.gz .'.format(NGINX_VERSION),
        
        # install uwsgi
        'tar xf uwsgi-{}.tar.gz'.format(UWSGI_VERSION),
        'cd uwsgi-{}'.format(UWSGI_VERSION),
        'python2.7 uwsgiconfig.py --build',
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
    server.system(session_id, 'bash -ec "{}"'.format('; '.join(install_steps).replace('"', r'\"')))
    
    # install nginx.conf and uwsgi.ini
    nginx_conf = (NGINX_CONF
        .replace('APPNAME', app_name)
        .replace('PORT', str(app['port']))
        .replace('DIR', app_dir)
        .replace('HOME', '/home/{}'.format(username))
    )
    uwsgi_ini = (UWSGI_INI
        .replace('DIR', app_dir)
        .replace('APPNAME', app_name)
        .replace('HOME', '/home/{}'.format(username)))
    server.write_file(session_id, 'conf/nginx.conf', nginx_conf, 'w')
    server.write_file(session_id, 'conf/uwsgi.ini', uwsgi_ini, 'w')
    server.write_file(session_id, 'conf/supervisord.conf', SUPERVISOR_CONFIG.replace('DIR', app_dir).replace('APPNAME', app_name), 'w')
    server.write_file(session_id, 'reload-app', RELOAD_APP.replace('DIR', app_dir).replace('APPNAME', app_name), 'w')
    server.write_file(session_id, 'app/wsgi.py', SAMPLE_APP, 'w')
    
    # set up app
    server.system(session_id, 'chmod +x reload-app')
    server.system(session_id, 'ln -s $PWD/conf/supervisord.conf $HOME/supervisor/app_APPNAME.conf'.replace('APPNAME', app_name))
    
    # load app
    server.system(session_id, '$HOME/bin/supervisorctl update')
    
    # create database if required
    # if 'postgres' in extra_info:
    #     db_name = db_user = '%s_%s' % (username, app_name)
    
    print app['id']

def delete(account, app_name, autostart, extra_info, password, server, session_id, username):
    # Delete application and database.
    try:
        server.system('unlink $HOME/supervisor/app_APPNAME.conf'.replace('APPNAME', app_name))
        server.system('$HOME/bin/supervisorctl update')
    except:
        pass
    
    server.delete_app(session_id, app_name)
    
    try:
        server.delete_db(session_id, '%s_%s' % (username, app_name), 'postgres')
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
            server.delete_app(session_id, app_name)
        except:
            pass
        # print the exception
        from traceback import print_exc
        print_exc(sys.stdout)
# -----END WEBFACTION INSTALL SCRIPT-----