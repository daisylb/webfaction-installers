"""
This file should be installed at ~/lib/python2.7
"""

from os.path import expanduser
from collections import namedtuple
import xmlrpclib
from traceback import print_exception
import sys

WebfactionArgs = namedtuple("WebfactionArgs", ("action", "username", "password", "machine", "app_name", "autostart", "extra_info"))

# normally, import side effects are evil
# but we want to redirect stdout/stderr ASAP, as we can't get to it otherwise
_real_stdout = sys.stdout
sys.stdout = open(expanduser('~/.last-install-output'), 'w')
sys.stderr = sys.stdout



class ApiPassthrough (object):
	def __init__(self, username, password, machine):
		self.server_proxy = xmlrpclib.ServerProxy('https://api.webfaction.com/')
		self.session_id, self.account = self.server_proxy.login(username, password, machine)
	
	def __getattr__(self, name):
		"""Wraps function calls to automatically insert the session ID as first argument."""
		def wrap(*args):
			return getattr(self.server_proxy, name)(self.session_id, *args)
		return wrap

class WebfactionInstaller (object):
	app_id = None
	debug = False
	
	def run(self, *args):
		"""Initiate the installation process.
		
		This should be called from an 'if __name__ == "__main__"' section in the actual script.
		"""
		
		self.args = WebfactionArgs(*args)
		self.api = ApiPassthrough(self.args.username, self.args.password, self.args.machine)
		
		# wrap the actual installer steps in a catch-all exception handler
		try:
			if self.args.action == "create":
				self._pre_create()
				self.create()
				
				# on success, print the app ID
				if self.app_id is None:
					self.fail("Script completed successfully, but did not set the self.app_id value.")
				_real_stdout.write(str(self.app_id))
				
			elif self.args.action == "delete":
				self._pre_delete()
				self.delete()
				self._perform_actual_deletion()
				
			else:
				self.fail("Unexpected first argument: {}".format(self.args.action))
				
		except BaseException:
			self.fail(exc_info=sys.exc_info())
	
	def _pre_create(self):
		pass
	
	def create(self):
		pass
	
	def _pre_delete(self):
		pass
	
	def delete(self):
		pass
	
	def _perform_actual_deletion(self):
		self.api.delete_app(self.args.app_name)
			
	def fail(self, message=None, exc_info=None):
		"""Error handling code.
		
		Webfaction is extremely picky about what installer scripts do or do not output,
		and much of this pickiness is not documented.
		
		We're not allowed to print anything to standard output or standard error, but we
		can write to files.
		
		This method writes to a file a message (if given), as well as the contents of
		stdout and stderr (which we cheekily redirect to StringIO instances).
		"""
		with open(expanduser('~/install-script-error.txt'), 'w') as f:
			if message is not None:
				# Write the given message.
				error_string = str(message)
				f.write("Installing your application encountered the following error:\n")
				f.write(error_string)
			else:
				# Write a traceback.
				f.write("Installing your application encountered an error.\n")
			
			# if there was an exception, print the traceback
			print_exception(exc_info[0], exc_info[1], exc_info[2], file=f)
		
		# Try to delete the app if possible
		if not self.debug:
			if self.args.action == "create":
				try:
					self._pre_delete()
					self.delete()
				except:
					pass
			try:
				self._perform_actual_deletion()
			except:
				pass
		
		# exit with an error
		exit(1)

class CustomAppOnPortInstaller (WebfactionInstaller):
	def _pre_create(self):
		self.base_app = self.api.create_app(self.args.app_name, 'custom_app_with_port', False, '')
		self.app_id = self.base_app['id']
		self.port = self.base_app['port']