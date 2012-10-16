# webfaction-installers

Install scripts for use on WebFaction

## Notes on writing WebFaction installers

- They must begin with the following header:

		#!/usr/local/bin/python2.7
		# -----BEGIN WEBFACTION INSTALL SCRIPT-----
		#!/usr/local/bin/python2.7
		
	This allows them to be copy-pasted or used as a remote URL.
- You cannot use tabs for indentation.
- Sending any output to stderr will result in failure with an unhelpful generic error message. To display helpful error message, wrap everything in a `try .. except BaseException` and print the exception to stdout.