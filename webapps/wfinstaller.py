from sys.path import expanduser
from collections import namedtuple
import xmlrpclib
from traceback import print_exc

WebfactionArgs = namedtuple("WebfactionArgs", ("action", "username", "password", "machine", "app_name", "autostart", "extra_info"))

class ApiPassthrough (object):
	def __init__(self, username, password, machine):
		self.server_proxy = xmlrpclib.ServerProxy('https://api.webfaction.com/')
		self.session_id, self.account = self.server_proxy.login(username, password, machine)
	
	def __getattr__(self, name):
		"""Wraps function calls to automatically insert the session ID as first argument."""
		def wrap(*args):
			return getattr(self.raw_server_proxy, name)(self.session_id, *args)
		return wrap

class WebfactionInstaller (object):
	app_id = None
	
	def run(self, *args):
		"""Initiate the installation process.
		
		This should be called from an 'if __name__ == "__main__"' section in the actual script.
		"""
		
		self.args = WebfactionArgs(args)
		self.api = ApiPassthrough(self.args.username, self.args.password, self.args.machine)
		
		# wrap the actual installer steps in a catch-all exception handler
		try:
			if self.args.action == "install":
				self._pre_install()
				self.install()
				
				# on success, print the app ID
				if self.app_id is None:
					self.fail("Script completed successfully, but did not set the self.app_id value.")
				print str(self.app_id)
				
			elif self.args.action == "remove":
				self._pre_remove()
				self.remove()
				self._perform_actual_removal()
				
			else:
				self.fail("Unexpected first argument: {}".format(self.args.action))
				
		except BaseException as e:
			self.fail()
	
	def _pre_install(self):
		pass
	
	def install(self):
		pass
	
	def _pre_remove(self):
		pass
	
	def remove(self):
		pass
	
	def _perform_actual_removal(self):
		self.api.delete_app(self.args.app_name)
			
	def fail(message = None):
		"""Error handling code.
		
		Webfaction is extremely picky about what installer scripts do or do not output,
		and much of this pickiness is not documented.
		
		We're not allowed to print anything to standard output or standard error, but we
		can write to files.
		
		Writes a message if given, the current or last exception otherwise.
		"""
			
		if message is not None:
			# Write the given message.
			error_string = str(message)
			with open(expanduser('~/install-script-error.txt'), 'w') as f:
				f.write("Installing your application encountered the following error:\n")
				f.write(error_string)
				f.write("\n")
		else:
			# Write a traceback.
			with open(expanduser('~/install-script-error.txt'), 'w') as f:
				f.write("Installing your application encountered the following exception:\n")
				print_exc(f)
				f.write("\n")
		
		exit(1)

class CustomAppOnPortInstaller (WebfactionInstaller):
	def _pre_install(self):
		self.base_app = server.create_app(self.args.app_name, 'custom_app_with_port', False, '')
		self.app_id = self.base_app['id']