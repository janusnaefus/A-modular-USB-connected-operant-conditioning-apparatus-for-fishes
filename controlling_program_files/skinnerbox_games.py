
from datetime import datetime
from datetime import timedelta
import time
import threading
import json
import sys
import skinnerbox_errors as errors
import skinnerbox_interThreadCommunication as interThreadCom
import re
import pandas as pd
import os

# converts a string to a timedelta object (see timedelta)
def str_to_timedelta(s):
	return timedelta(hours = s.hour,  minutes = s.minute,  seconds=s.second)

def st(time):
	# "string to time" - convert a string of given format to a datetime object
	return datetime.strptime(time, '%H:%M:%S').time()

def tdt(time):
	# "time to datetime" - convert a time to a datetime object (with todays date), allwing for addition and substraction
	now = datetime.now()
	return datetime(now.year, now.month, now.day, time.hour, time.minute, time.second)

# this is a function that is used by Timer objects (see threading). it is called after a time delay by a separate thread and sets a given event.s
def wait_for_timeout(e):
	e.set()

# write data to a debug log. just calls print and flushes
# flushing is necessary because the bash script on the pi redirects the output to a file in the network folder
# this is done in order to read the output remotely (ssh does not work on eduroam...)
# without flushing, it will not work
def write_debug_log(str):
	print str
	sys.stdout.flush()

# just a shortcut for the above function
def p(str):
	write_debug_log(str)

def col(array, c):
	return [row[c] for row in array]

class schedule:
	@staticmethod
	def read_schedule(_config, _name):
		# creates a schedule and fills it with the settings read from _config in section _name
		# it also creates the games contained in this schedule, which will in turn create the tasks contained in the games.
		ret = schedule(_name)

		# the toDoList lists tasks, their time, and whether they still have to be done.
		ret.toDoList       = pd.DataFrame(columns = ['game', 'time', 'status'])

		if not _config.has_section(_name):
			raise errors.MinorConfigError("could not find " + _name)

		numGames = 0
		for option in _config.options(_name):
			if 'game' in option:
				numGames = numGames + 1
		if numGames == 0:
			raise errors.MinorConfigError(_name + " does not contain any games")

		if not _config.has_option(_name, 'run later if missed'):
			ret.run_later_if_missed = True
		elif _config.get(_name, 'run later if missed') == 'False':
			ret.run_later_if_missed = False
		elif _config.get(_name, 'run later if missed') == 'True':
			ret.run_later_if_missed = True
		else:
			raise errors.MinorConfigError(_name + ": option \"run later if missed\" specified, but invalid (should be either True or False)")
			
			
		for option in _config.options(_name):
			if 'game' in option:
				# the same game can be run at several schedules. this is specified by adding .1, .2 etc behind the game name. this suffix is removed here
				this_game      = re.sub('\.[0-9]', '', option)
				values         = json.loads(_config.get(_name, option))
				schedule_kind  = values[0]

				if schedule_kind == "specific":
					if len(values) == 1:
						raise errors.MinorConfigError(_name + " set to run at specific times, but time list is empty.")
					else:
						for v in values[1:]:
							this_time = st(v)
							if this_time < datetime.now().time():
								this_status = 'entered_too_late'
							else:
								this_status = 'to_do'
								ret.toDoList = ret.toDoList.append({'game': this_game, 'time': this_time, 'status': this_status}, ignore_index=True)

				elif schedule_kind == "interval":
					interval_start = st(values[1])
					interval_end   = st(values[2])
					interval       = str_to_timedelta(st(values[3]))
					if interval_start > interval_end:
						raise errors.MinorConfigError(_name + ": interval ends (" + str(interval_start) + ") before it starts (" + str(interval_end) + ").")

					this_time = interval_start
					while this_time < interval_end:
						if this_time < datetime.now().time():
							this_status = 'entered_too_late'
						else:
							this_status = 'to_do'
						ret.toDoList = ret.toDoList.append({'game': this_game, 'time': this_time, 'status': this_status}, ignore_index=True)
						this_time = (tdt(this_time) + interval).time()

				elif schedule_kind == "now":
					this_time = datetime.now().time()
					this_status = 'to_do'
					ret.toDoList = ret.toDoList.append({'game': this_game, 'time': this_time, 'status': this_status}, ignore_index=True)

				else:
					raise errors.MinorConfigError(_name + " contains an invalid section: \"" + str(values[0]) + "\"\nIt should be \"now\", \"interval\" or \"specific\"")

		ret.toDoList = ret.toDoList.sort_values(['time'], axis=0, ascending=True)
		ret.print_tasks()
		
		# see which games have been specified in the schedule, and create these games
		ret.gameList = {} # a dictionary, linking game structures to their names
		for g in ret.toDoList['game'].unique():
			if _config.has_section(g):
				ret.gameList[g] = game.read_game(_config, g)
			else:
				raise errors.MinorConfigError(_name + ": " + g + " not found")


		return ret

	def __init__(self, _name):
		self.name = _name

	def next():
		pass

	def next_game_index(self):
		# return the index of the next game that has to be played.

		# get all entries that have to be done yet
		all_to_do  = self.toDoList[self.toDoList['status'] == 'to_do']
		# if there are none, return none, but if it is also midnight, reset them first.
		if all_to_do.shape[0] == 0:
			if datetime.now().time() < st("00:01:00"):
				self.toDoList['status'] = 'to_do'
			return None
		# if there are any, return the index of the one with the lowest time
		else:
			next_to_do = all_to_do[all_to_do['time'] == min(all_to_do['time'])].index.item()
			return next_to_do

	def mark_as_done(self):
		i = self.next_game_index()
		self.toDoList.at[i, 'status'] = 'done'
		p(self.toDoList)

	def print_tasks(self):
		p(self.name + " with " + str(self.toDoList.shape[0]) + " tasks:")
		p(self.toDoList)
			
	def gamePending(self):
		i = self.next_game_index()
		if i == None:
			return None
		else:
			if self.toDoList.at[i, 'time'] < datetime.now().time():
				return self.gameList[self.toDoList.at[i, 'game']]
	

###########
class task:
	@staticmethod
	def read_task(_config, _name):
		
		# creates a task and fills it with the settings read from _config in section _name
		ret = task(_name)

		def load_setting(_setting):
			if _config.has_option(_name, _setting):
				return _config.get(_name, _setting)
			else:
				return _config.get("default task settings", _setting)

		ret.button_index            = int(load_setting("button_index"))
		ret.color                   = json.loads(load_setting("color"))
		ret.button_threshold        = load_setting("button_threshold")
		ret.command_signal_duration = load_setting("command_signal_duration")
		ret.reward_signal_duration  = load_setting("reward_signal_duration")
		ret.button_active_duration  = str_to_timedelta(st(load_setting("button_active_duration")))
		ret.reward_index            = int(load_setting("reward_index"))
		ret.reward_method_str       = load_setting("reward_method")
		ret.reward_amount           = load_setting("reward_amount")
		ret.break_duration          = str_to_timedelta(st(load_setting("break_duration")))
		ret.max_n                   = int(load_setting("max_n"))
		ret.max_time                = str_to_timedelta(st(load_setting("max_time")))
		ret.delay_after_last_successful_trial  = str_to_timedelta(st(load_setting("delay_after_last_successful_trial")))
		ret.delay_after_last_unsuccessful_trial  = str_to_timedelta(st(load_setting("delay_after_last_unsuccessful_trial")))
		ret.override_max_time       = int(load_setting("override_max_time"))
		#ret.camera                  = load_setting("camera")


		return ret

	def __init__(self, _name):
		self.name  = _name
		self.itc = interThreadCom.interThreadCom()

	def run(self, _tank):
		
		# run a task, i.e. n_trials button pressing quests on b followed by feeding on f
		# klick - light b - feed on f if pushed before button_timeout, otherwise unlight b
		# repeat after interval until n_trials
		# abort and return when max_time passes
		
		# if wait_after_last_trial is set to 1, the break_duration is also waited for after the last trial has completed. this can be used to chain several trials together in the game without having to write a separate loop that checks for event changes.
		# if no game_end_event is passed to this function, it will create one itself, using max_time	

		# if camera is set to "picamera", load the required module and start recording
		#if self.camera == "picamera":
		#	p("starting to record video")
		#	start_time = datetime.now()
		#	filename = os.path.dirname(os.path.realpath(__file__)) + '/videos/' + start_time.strftime('%y%m%d_%H%M%S_%f') + '.h264'
		#	import picamera
		#	camera = picamera.PiCamera()
		#	camera.resolution = (1296, 730)#(1296, 972)#(1920, 1080) #(640, 480)
		#	camera.framerate  = 30
		#	camera.start_recording(filename)

		b                     = _tank.inDev[self.button_index]
		reward_device         = _tank.outDev[self.reward_index]
		fish                  = str(_tank.fishList[self.button_index])
		times_played          = 0
		reward_method         = eval("reward_device." + self.reward_method_str)

		logfile               = open(_tank.logfile_name, "a")

		b.set_thr(self.button_threshold)

		# the data about the current task, to be printed to the log file each time something happens along with what happens
		# note that this should correspond to the header written by load_tank
		temp = []
		temp.append(self.name)
		temp.append(_tank.name)
		temp.append(str(self.button_index))
		temp.append(fish)
		temp.append(b.pid())
		temp.append(str(self.color[0]))
		temp.append(str(self.color[1]))
		temp.append(str(self.color[2]))
		temp.append(str(self.button_threshold))
		temp.append(str(self.command_signal_duration))
		temp.append(str(self.reward_signal_duration))
		temp.append(str(self.button_active_duration))
		temp.append(str(self.reward_index))
		temp.append(reward_device.pid())
		temp.append(self.reward_method_str)
		temp.append(str(self.reward_amount))
		temp.append(str(self.break_duration))
		temp.append(str(self.max_n))
		temp.append(str(self.max_time))
		temp.append(str(self.delay_after_last_successful_trial))
		temp.append(str(self.delay_after_last_unsuccessful_trial))
		temp.append(str(self.override_max_time))

		data = ''
		for i in range(0, len(temp)):
			data = data + temp[i]
			if not i == len(temp) - 1:
				data = data + ','

		def write_data_log(_event, _value1 = None, _value2 = None):
			temp = '\n' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + ',' + _event + ',' + str(_value1) + ',' + str(_value2) + ',' + str(times_played) + ',' + data
			p(temp)
			logfile.write(temp)
			logfile.flush()

		write_data_log('start')
			
		light_button_event        = threading.Event()
		unlight_button_event      = threading.Event()
		send_reward_signal_event  = threading.Event()
		send_command_signal_event = threading.Event()
		feeding_event             = threading.Event()
		last_trial_done_event     = threading.Event()
		game_end_event            = threading.Event()

		# try to get rid of the game_end_event and wait_for_timeout, use game_timer.finished instead
		game_timer        = threading.Timer(interval = self.max_time.total_seconds(), function = wait_for_timeout, args = (game_end_event,))
		game_timer.name   = _tank.name + "_game_timer"
		game_timer.daemon = True
		game_timer.start()

		send_command_signal_event.set()
		
		# play the game 
		while 1:
			# poll for messages in the inter thread communication. if they are errors about devices used in this task, output this error and return
			if self.itc.has_messages():
				thisTankIsAffected = False
				for message in self.itc.read_messages():
					if reward_device.pid() in message or b.pid() in message:
						thisTankIsAffected = True
						last_message = message
						p("\n\t!!!\t")
						p(  "\t!!!\t" + message)
						p(  "\t!!!\t\n")
						self.itc.remove_messages(message)
				if thisTankIsAffected:
					write_data_log('stop_error', last_message)
					self.itc.reload_tank_flags[_tank.name].set()
					break

			# if all tanks have to stop (e.g. because of a keyboard interrupt) return
			if self.itc.stop_all_tanks_flag.isSet():
				write_data_log('stop_aborted')
				p("itc sais stop. returning...")
				break

			# if the tank this task is running on has to be reloaded, exit the game
			if self.itc.reload_tank_flags[_tank.name].isSet() or self.itc.reload_all_tanks_flag.isSet():
				write_data_log('stop_aborted')
				break

			# if the fish has played enough, exit the game
			if last_trial_done_event.isSet():
				write_data_log('stop_last_trial_done')
				break

			# if the time is up, end the game, except if the fish has just pressed the button. otherwise, wait until he got his reward.
			if game_timer.finished.isSet():
				if not send_reward_signal_event.isSet() and not feeding_event.isSet():
					try: #if you try to see whether trial_end_timer is alive, and it has not been defined yet, this will throw an error
						if not (trial_end_timer.is_alive() and self.override_max_time == 1):
							write_data_log('stop_time_is_up')
							break
					except UnboundLocalError:
						pass
			
			# send a command signal if it need be, and light the button afterwards
			if send_command_signal_event.isSet():
				send_command_signal_event.clear()
				b.klick(self.command_signal_duration, light_button_event)

			# light the button if it need be
			if light_button_event.isSet():
				write_data_log('armed')
				light_button_event.clear()
				b.led_on(self.color[0], self.color[1], self.color[2])
				time_armed                  =  datetime.now()
				unlight_button_timer        =  threading.Timer(self.button_active_duration.total_seconds(), wait_for_timeout, args = (unlight_button_event,))
				unlight_button_timer.name   = _tank.name + "_unlight_button_timer"
				unlight_button_timer.daemon = True
				unlight_button_timer.start()

			# unlight the button if it need be (if it hasnt been pressed for button_active_duration)
			if unlight_button_event.isSet():
				write_data_log('disarmed')
				unlight_button_event.clear()
				b.led_off()
				times_played += 1
				if times_played < self.max_n:
					light_button_timer        = threading.Timer(self.break_duration.total_seconds(), wait_for_timeout, args = (send_command_signal_event,))
					light_button_timer.name   = _tank.name + "_light_button_timer"
					light_button_timer.daemon = True
					light_button_timer.start()
				elif self.delay_after_last_unsuccessful_trial.total_seconds() > 0:
					trial_end_timer        = threading.Timer(self.delay_after_last_unsuccessful_trial.total_seconds(), wait_for_timeout, args = (last_trial_done_event,))
					trial_end_timer.name   = _tank.name + "_trial_end_timer"
					trial_end_timer.daemon = True
					trial_end_timer.start()
				else:
					last_trial_done_event.set()

			# send a reward signal if it need be, and feed afterwards
			if send_reward_signal_event.isSet():
				send_reward_signal_event.clear()
				b.klick(self.reward_signal_duration, threading.Event())
				feeding_event.set()

			# feed the fish if it need be. check if it can play again, and start a timeout to light the button if so. if not, leave the game
			if feeding_event.isSet():
				feeding_event.clear()
				feeding_start = datetime.now()
				fed_duration, fed_amount = reward_method(self.reward_amount)
				write_data_log('fed', fed_duration, fed_amount)
				times_played += 1
				if times_played < self.max_n:
					light_button_timer        = threading.Timer(self.break_duration.total_seconds(), wait_for_timeout, args = (send_command_signal_event,))
					light_button_timer.name   = _tank.name + "_light_button_timer"
					light_button_timer.daemon = True
					light_button_timer.start()
				elif self.delay_after_last_successful_trial.total_seconds() > 0:
					trial_end_timer       = threading.Timer(self.delay_after_last_successful_trial.total_seconds(), wait_for_timeout, args = (last_trial_done_event,))
					trial_end_timer.name   = _tank.name + "_trial_end_timer"
					trial_end_timer.daemon = True
					trial_end_timer.start()
				else:
					last_trial_done_event.set()

			
			# if a button is triggered:
			# turn it off and send a reward signal. this will in turn trigger feeding of the fish and re-lighting of the button.
			if b.trig():
				try:
					unlight_button_timer.cancel()
				except:
					pass
				trigger_delay =  (datetime.now() - time_armed).total_seconds()
				write_data_log('triggered', trigger_delay)
				b.led_off()
				send_reward_signal_event.set()


		# turn all buttons off
		b.led_off()

		# cancel running timers
		try:
			game_timer.cancel()
		except:
			pass
		try:
			unlight_button_timer.cancel()
		except:
			pass
		try:
			light_button_timer.cancel()
		except:
			pass
		try:
			trial_end_timer.cancel()
		except:
			pass

		logfile.close()

		
		# if camera is "picamera", stop the recording after 5 seconds.
		#if self.camera == "picamera":
		#	camera.wait_recording(5)
		#	camera.stop_recording()
		
		# done successfully
		return 0

###########
class game:
	@staticmethod
	def read_game(_config, _name):
		# creates a game and fills it with the game-specific settings and tasks specified in section _name
		# each game section specifies which tasks have to be played in that game
		# see whether these tasks are present. if so, load them and create the game

		ret           = game(_name)
		ret.taskList  = []

		for t in _config.options(_name):
			if t in _config.sections():
				ret.taskList.append(task.read_task(_config, t))
			else:
				raise errors.MinorConfigError("Could not find " + t)

		ret.numTasks = len(ret.taskList)
		return ret

	def __init__(self,  _name):
		self.name = _name
		
	def run(self, _tank):
		for t in self.taskList:
			p('game running ' + t.name)
			t.run(_tank)




###########
class tank:
	@staticmethod
	def load_tank(_config, _name, _dev):
		# create a tank by reading section _name from the _config
		p("\nloading " + _name)
		p(  "########" + "#" * len(_name))

		ret       = tank(_name)
		ret.itc   = interThreadCom.interThreadCom()

		# each tank section has a moduleList, specifying which modules are attached to this tank
		# see whether these are attached to the responsible controller (i.e. present in _dev)
		moduleListFound = []
		moduleListGiven = json.loads(_config.get(_name, "moduleList"))

		if len(moduleListGiven) == 0:
			raise errors.MinorConfigError("The module list for " + ret.name + " is empty.")

		p("need " + str(len(moduleListGiven)) + " devices:")
		for m_g in moduleListGiven:
			p("\t" + m_g)
			module_found = False
			for n, d in _dev.iteritems():
				if d.pid() == m_g:
					moduleListFound.append(d)
					module_found = True
			if not module_found:
				raise errors.MinorConfigError("Unable to load module " + m_g + ".")

		# assign the found devices to input (BUTTON) and output (other) devices
		ret.inDev       = []
		ret.outDev      = []
		for i, m_g in enumerate(moduleListGiven):
			if 'BUTTON' in m_g:
				ret.inDev.append(moduleListFound[i])
			else:
				ret.outDev.append(moduleListFound[i])
		ret.numInDev  = len(ret.inDev)
		ret.numOutDev = len(ret.outDev)
		p("found " + str(ret.numInDev) + " input devices:")
		for i in ret.inDev:
			p("\t" + i.pid())
		p("found " + str(ret.numInDev) + " output devices:")
		for i in ret.outDev:
			p("\t" + i.pid())

		# also, each tank section specifies which fish are in the tank.
		ret.fishList  = json.loads(_config.get(_name, "fishList"))
		ret.numFish   = len(ret.fishList)
		if ret.numFish == 0:
			raise errors.MinorConfigError("The fish list for " + ret.name + " is empty.")
		
		p("found " + str(ret.numInDev) + " fish:")
		for i, n in enumerate(ret.fishList):
			p("\t" + n + '\t' + ret.inDev[i].pid() + '\t' + ret.outDev[i].pid())

		# also, it specifies which schedule has to be played on that tank
		ret.schedule  = schedule.read_schedule(_config, _config.get(_name, "schedule"))

		# a tank opens a new file when it is created, writing information about the session to a header and allowing the running tasks to log data to it.

		# open a file and write a header containing the current setings
		# the tasks to be played will then add the data to the same file
		ret.logfile_name = ret.itc.get_basedir() + "/" + ret.name + datetime.now().strftime('_%Y%m%d_%H%M%S_%f') + ".txt"
		ret.logfile      = open(ret.logfile_name, "w+")

		# write some general information to the logfile
		ret.logfile.write("[general]")
		ret.logfile.write("\nprogram_version: " + ret.itc.get_program_version())
		ret.logfile.write("\ndate: " + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))

		# a function that writes all options of a given section to the config file
		def write_section(s):
			ret.logfile.write("\n\n[" + s + "]")
			for o in _config.options(s):
				ret.logfile.write("\n" + o + ": ")
				ret.logfile.write(_config.get(s, o))
		
		# write tank information to header
		write_section(_name)
		# write schedule information
		write_section(_config.get(_name, "schedule"))
		# write game information for each game in schedule
		# note that the schedule contains options that are not games. filter those out
		gamesWritten = []
		for g in _config.options(_config.get(_name, "schedule")):
			if 'game' in g:
				# a schedule can contain the same game several times, and this is specified by a .1, .2 etc suffix. remove this suffix to find the game.
				g = re.sub('\.[0-9]', '', g)
				# do not write the same gime twice
				if not g in gamesWritten:
					gamesWritten.append(g)
					write_section(g)
					# also write all tasks in the game
					for t in _config.options(g):
						write_section(t)
		# write default task information
		write_section("default task settings")

		ret.logfile.write("\n\n[data]")

		# write the header for task data
		# note that this should correspond to the data that the task will log
		# first, list all items to be contained in the header
		temp = []
		temp.append("time")
		temp.append("event")
		temp.append("value1")
		temp.append("value2")
		temp.append("times_played")
		temp.append("task")
		temp.append("tank")
		temp.append("button_index")
		temp.append("fish")
		temp.append("button")
		temp.append("red")
		temp.append("green")
		temp.append("blue")
		temp.append("button_threshold")
		temp.append("command_signal_duration")
		temp.append("reward_signal_duration")
		temp.append("button_active_duration")
		temp.append("reward_index")
		temp.append("reward_device")
		temp.append("reward_method")
		temp.append("reward_amount")
		temp.append("break_duration")
		temp.append("max_n")
		temp.append("max_time")
		temp.append("delay_after_last_successful_trial")
		temp.append("delay_after_last_unsuccessful_trial")
		temp.append("override_max_time")
		# join these items with a comma in between each
		data = ''
		for i in range(0, len(temp)):
			data = data + temp[i]
			if not i == len(temp) - 1:
				data = data + ','
		# write this header to the logfile
		ret.logfile.write("\n" + data)

		ret.logfile.close()

		return ret

	def __init__(self, _name):
		self.name  = _name

	def run(self):
		p(self.name + " running!")

		# play games or wait according to the schedule
		while True:
			game_pending = self.schedule.gamePending()
			if not game_pending == None:
				game_pending.run(self)
				self.schedule.mark_as_done()
			# if the flag to stop all tanks or the one to stop this tank is set, exit the loop
			if self.itc.reload_all_tanks_flag.isSet():
				break
			if self.itc.stop_all_tanks_flag.isSet():
				break
			if self.itc.reload_tank_flags[self.name].isSet():
				break
		# if the loop is exited, close your devices and return
		for d in self.inDev:
			d.close_device()
		for d in self.outDev:
			d.close_device()
		return


