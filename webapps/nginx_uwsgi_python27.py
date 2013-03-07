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

from wfinstaller import CustomAppOnPortInstaller

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
      uwsgi_param UWSGI_SCHEME $http_x_forwarded_proto;
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
[group:app-APPNAME]
programs=app-APPNAME-uwsgi,app-APPNAME-nginx

[program:app-APPNAME-uwsgi]
command=DIR/bin/uwsgi --ini DIR/conf/uwsgi.ini
priority=1
autorestart=true
; these two are to stop uwsgi zombies
stopsignal=QUIT
stopasgroup=true

[program:app-APPNAME-nginx]
command=DIR/bin/nginx -c DIR/conf/nginx.conf
priority=2
autorestart=true
"""

RELOAD_APP = """
#!/bin/bash
set -e
if test -f DIR/app/requirements.txt; then
    DIR/bin/pip install -U -r DIR/app/requirements.txt
fi
if test -f DIR/app/update.sh; then
    (source DIR/bin/activate.sh && cd DIR/app && bash update.sh)
fi
supervisorctl restart app-APPNAME:*
"""

SAMPLE_APP = """
import sys

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield 'Hello World!\\\\n' + sys.version + '\\\\n' + sys.executable + '\\\\n'
"""

UWSGI_VERSION = '1.3'
NGINX_VERSION = '1.3.6'

class NginxUwsgiPython27Installer (CustomAppOnPortInstaller):
    def create(self):
        app_dir = "/home/{}/webapps/{}".format(self.args.username, self.args.app_name)
        
        install_steps = (
            # make virtualenv and directories
            '~/bin/virtualenv --python=python2.7 .',
            'mkdir build conf pid sock app tmp',
            
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
            '../../bin/python2.7 uwsgiconfig.py --build',
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
            'rm -rf build',
        )
        
        # run install steps
        commands = 'bash -ec "{}"'.format('; '.join(install_steps).replace('"', r'\"'))
        self.api.system(commands)
        
        # install nginx.conf and uwsgi.ini
        nginx_conf = (NGINX_CONF
            .replace('APPNAME', self.args.app_name)
            .replace('PORT', str(self.port))
            .replace('DIR', app_dir)
            .replace('HOME', '/home/{}'.format(self.args.username))
        )
        uwsgi_ini = (UWSGI_INI
            .replace('DIR', app_dir)
            .replace('APPNAME', self.args.app_name)
            .replace('HOME', '/home/{}'.format(self.args.username)))
        self.api.write_file('conf/nginx.conf', nginx_conf, 'w')
        self.api.write_file('conf/uwsgi.ini', uwsgi_ini, 'w')
        self.api.write_file('conf/supervisord.conf', SUPERVISOR_CONFIG.replace('DIR', app_dir).replace('APPNAME', self.args.app_name), 'w')
        self.api.write_file('reload-app', RELOAD_APP.replace('DIR', app_dir).replace('APPNAME', self.args.app_name), 'w')
        self.api.write_file('app/wsgi.py', SAMPLE_APP, 'w')
        
        # set up app
        self.api.system('chmod +x reload-app')
        self.api.system('ln -s $PWD/conf/supervisord.conf $HOME/supervisor/app_APPNAME.conf'.replace('APPNAME', self.args.app_name))
        
        # load app
        self.api.system('$HOME/bin/supervisorctl update')

    def delete(self):
        # Delete application and database.
        try:
            self.api.system('unlink $HOME/supervisor/app_APPNAME.conf'.replace('APPNAME', self.args.app_name))
            self.api.system('$HOME/bin/supervisorctl update')
        except:
            pass

if __name__ == '__main__':
    import sys
    NginxUwsgiPython27Installer().run(*sys.argv[1:])
# -----END WEBFACTION INSTALL SCRIPT-----