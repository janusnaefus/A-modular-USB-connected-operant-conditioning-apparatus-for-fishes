import threading

class interThreadCom:
	reload_all_tanks_flag   = threading.Event()
	stop_all_tanks_flag     = threading.Event()
	stop_file_monitor_flag  = threading.Event()
	reload_config_file_flag = threading.Event()
	messages                = []
	reload_tank_flags       = {}
	basedir = None
	program_version = None

	def send_message(self, _message):
		interThreadCom.messages.append(_message)

	def has_messages(self):
		if len(interThreadCom.messages) > 0:
			return True
		else:
			return False

	def read_messages(self):
		return interThreadCom.messages

	def remove_messages(self, _messages):
		for mg in _messages:
			for i in range(1,len(interThreadCom.messages)):
				if mg == interThreadCom.messages[i]:
					del interThreadCom.messages[i]

	def set_basedir(self, _basedir):
		interThreadCom.basedir = _basedir

	def get_basedir(self):
		return interThreadCom.basedir

	def set_program_version(self, _program_version):
		interThreadCom.program_version = _program_version

	def get_program_version(self):
		return interThreadCom.program_version
