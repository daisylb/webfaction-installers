# webfaction-installers

- nginx_uwsgi_python27: Run WSGI apps on top of nginx and uwsgi. Designed to be automated with a SCM-based auto deploy process.
	- Put your app in the `app/` folder.
		- Make sure that there's a `wsgi.py` containing the wsgi callable as `application`.
		- Optionally, put a `requirements.txt` file in `app/`.
		- Optionally, put a `post-update` script in `app/`.
	- Run the `update` script.
	- Note: Currently runs stuff under 2.6, not 2.7.

## Installers To Do

- General redirect using extra_info (eg `redirect=http://example.com/`, `redirect=http://example.net/my/url append-path=no`)
- Redirect to HTTPS
- Sentry

## Notes on writing WebFaction installers

- They must begin with the following header:

		#!/usr/local/bin/python2.7
		# -----BEGIN WEBFACTION INSTALL SCRIPT-----
		#!/usr/local/bin/python2.7
		
	This allows them to be copy-pasted or used as a remote URL.
- You cannot use tabs for indentation.
- Sending any output to stderr will result in failure with an unhelpful generic error message. To display helpful error message, wrap everything in a `try .. except BaseException` and print the exception to stdout.