#!/usr/bin/env bash

# SUPERVISOR
# Installs the Supervisor process manager.
# All files in ~/supervisor/ will be included into the config,
# so place per-app configs there rather than editing the main config file.

# install
easy_install-2.7 supervisor

# make req'd directories
mkdir -p ~/sock ~/pid ~/supervisor ~/etc

# config file
read -r -d '' SUPERVISOR_CFG <<'EOF'
[unix_http_server]
file=__HOME__/sock/supervisor.sock   ; (the path to the socket file)
chmod=0700                 ; socket file mode (default 0700)

[supervisord]
logfile=__HOME__/logs/user/supervisord.log ; (main log file;default $CWD/supervisord.log)
logfile_maxbytes=50MB        ; (max main logfile bytes b4 rotation;default 50MB)
logfile_backups=10           ; (num of main logfile rotation backups;default 10)
loglevel=info                ; (log level;default info; others: debug,warn,trace)
pidfile=__HOME__/pid/supervisord.pid ; (supervisord pidfile;default supervisord.pid)
nodaemon=false               ; (start in foreground if true;default false)
minfds=1024                  ; (min. avail startup file descriptors;default 1024)
minprocs=200                 ; (min. avail process descriptors;default 200)
environment=PATH=__PATH__

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix://__HOME__/sock/supervisor.sock ; use a unix:// URL  for a unix socket

[include]
files = __HOME__/supervisor/*
EOF
# ~/etc/supervisord.conf is one of the default config search locations
echo "$SUPERVISOR_CFG" | sed -e "s|__HOME__|$HOME|g" -e "s|__PATH__|$PATH|g" > ~/etc/supervisord.conf

# use cron to ensure supervisord is running
(crontab -l ; echo "0,20,40 * * * * $HOME/bin/supervisord -c $HOME/etc/supervisord.conf") | crontab -

# start
supervisord -c $HOME/etc/supervisord.conf
