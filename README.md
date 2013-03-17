# webfaction-installers

Various custom-webapp and utility installers for WebFaction's hosting platform.

## Utilities

- **pip** - Pip Installs Packages. Installs pip for Python 2.5-2.7 and 3.1-3.3. `bash <(wget -qO- https://github.com/adambrenecki/webfaction-installers/raw/master/utils/pip.sh)`
- **supervisor** - Manages processes, like daemontools or launchd, but doesn't need to run as pid 1. Use it to automatically restart your apps without waiting 20 minutes like Webfaction's default cron-based solution does. `bash <(wget -qO- https://github.com/adambrenecki/webfaction-installers/raw/master/utils/supervisor.sh)`

## Webapps

- **nginx_uwsgi_python27** - Run WSGI apps on top of nginx and uwsgi. Designed to be automated with a SCM-based auto deploy process. [install](https://my.webfaction.com/new-application?script_url=https%3A%2F%2Fgithub.com%2Fadambrenecki%2Fwebfaction-installers%2Fraw%2Fmaster%2Fwebapps%2Fnginx_uwsgi_python27.py)
	- Requires: supervisor, pip
- **sentry** - A logging app. [install](https://my.webfaction.com/new-application?script_url=https%3A%2F%2Fgithub.com%2Fadambrenecki%2Fwebfaction-installers%2Fraw%2Fmaster%2Fwebapps%2Fsentry.py)
	- Requires: supervisor, pip
	- Additional post-installation steps required - see the created file `webapps/<app_name>/sentry.conf.py`

## Installers To Do

- General redirect using extra_info (eg `redirect=http://example.com/`, `redirect=http://example.net/my/url append-path=no`)
- Redirect to HTTPS

## Notes on writing WebFaction webapp installers from scratch

- They must begin with the following header:

		#!/usr/local/bin/python2.7
		# -----BEGIN WEBFACTION INSTALL SCRIPT-----
		#!/usr/local/bin/python2.7
		
	This allows them to be copy-pasted or used as a remote URL.
- You cannot use tabs for indentation. (This doesn't appear to be the case anymore.)
- Contrary to what the official WebFaction docs say, returning any unexpected output on stdout, or any output at all on stderr, results in the script failing with a generic error message. The best way to record any information on failure is to write it to a file.

## Debugging a failed webapp install

WebFaction's custom installer system provides quite possibly the least helpful error messages in the world. To get around this, these installers will create a file called `install-script-error.txt` in your home directory when they fail, which contains a traceback.

The file `.last-install-output` is also created unconditionally, and the installer's output piped to it; if the installer fails too early for `install-script-error.txt` to be written, something useful is usually in here.