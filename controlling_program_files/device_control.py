# this file relies on having access to a network folder from which config files are read and output is written.
import serial
import glob
from datetime import datetime
from datetime import timedelta
import time
import ConfigParser
import json
import os
import sys
import threading
import skinnerbox
import skinnerbox_games
import random
import re
import skinnerbox_errors as errors
import skinnerbox_interThreadCommunication as interThreadCom

#  a dict mapping serial numbers (as found in the file /proc/cpuinfo) to device ids (as specified in the config file)
# this is also done in the file 'feeder_launcher_stage_2.sh', and the mapping here should correspond to the mapping in this file.
serial_numbers = {}
serial_numbers["00000000d0959c08"] = "PI_001"
serial_numbers["00000000ddb07dca"] = "PI_002"
serial_numbers["0000000023a916b3"] = "PI_003"
serial_numbers["0000000055128134"] = "PI_004"
serial_numbers["00000000d8ca3ccd"] = "PI_005"
serial_numbers["000000002bf030d6"] = "PI_006"
serial_numbers["Laptop"]           = "Laptop"


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

# this is a function that is used by Timer objects (see threading). it is called after a time delay by a separate thread and sets a given event.
def wait_for_timeout(e):
	e.set()

def detect_file_modification(_filename, _flag, _kill_flag):
	itc = interThreadCom.interThreadCom()
	# _flag is the event which is set when file called _filename has been changed
	file_mod  = os.path.getmtime(_filename)
	while True:
		time.sleep(2)
		# check whether the file exists
		if os.path.exists(_filename):
			new_file_mod  = os.path.getmtime(_filename)
			# if the modification date has changed, set the provided _flag
			if new_file_mod > file_mod:
				file_mod = new_file_mod
				_flag.set()
		# the _kill_flag indicates to this function that it should stop monitoring
		if _kill_flag.isSet():
			return



class devices:	
	def __init__(self):
		# the interThreadCom allows communication between parallel threads
		self.itc  = interThreadCom.interThreadCom()
		self.parse_id()
		self.check_files()

		# the config file is read by a ConfigParser. it will be opened later, depending on which machine this program is running on
		self.config     = ConfigParser.ConfigParser()
		# a dict to map port names to device instances
		self.deviceList = {}
		# a dict to map tank names to tank instances
		self.tankList   = {}
		self.read_protocol()

	def parse_id(self):
		# find the cpu's serial number and determine which controller this program is running on
		# the raspberry pi zero w has a unique serial number, stored in the file /proc/cpuinfo
		f = open('/proc/cpuinfo','r')
		hw_id = None
		for line in f:
			if line[0:6]=='Serial':
				hw_id = line[10:26]
		f.close()
		# on non-pi controllers, the file also exists, but does not contain a serial numer
		if hw_id == None:
			hw_id = 'Laptop'

		# determine the devices id from the dict given above
		self.id = serial_numbers[hw_id]
		p("working on " + self.id)

	def check_files(self):
		p("\nChecking files")
		p(  "##############")
		# set the working directory to the location of this file
		self.basedir = os.path.dirname(os.path.realpath(__file__))
		
		# from this, extract the program version, which should be supplied as a date in the format yymmdd_hhmm in the folder containing this file
		try:
			self.program_version = re.search('[0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9]', self.basedir.split('/')[-1]).group(0)
		# if this does not work (re.search returns None), take todays date instead.		
		except AttributeError:
			p("no program version specified in folder name. taking date instead")
			self.program_version = datetime.now().strftime("%y%d%m_%H%M")

		# set the basedir and program version on the itc (inter thread communication), for the tank threads to use
		self.itc.set_basedir(self.basedir)
		self.itc.set_program_version(self.program_version)

		self.debug_filename        = self.basedir + "/debug_"       + self.id + ".txt"
		self.reload_all_tanks_flag_filename  = self.basedir + "/reload_all_tanks_flag_" + self.id + ".txt"
		self.config_filename       = self.basedir + "/training_protocol.txt"
		self.debug_file            = open(self.debug_filename,  "a+")  # open the debug file for appending to it
		self.reload_all_tanks_flag_file      = open(self.reload_all_tanks_flag_filename, "w+")
		self.reload_all_tanks_flag_file.close()

		p("working directory: " + self.basedir)
		p("program version:   " + self.program_version)
		p("debug file:        " + self.debug_filename.split('/')[-1])
		p("reload all tanks flag:       " + self.reload_all_tanks_flag_filename.split('/')[-1])
		p("config file:       " + self.config_filename.split('/')[-1])

		# monitor_reload_flag will periodically check whether the file reload_flag has been modified, unless kill_monitor is set
		self.kill_monitor_reload_flag = threading.Event()
		self.monitor_reload_flag = threading.Thread(name = 'reload_all_tanks_monitor_thread', target = detect_file_modification, args = (self.reload_all_tanks_flag_filename, self.itc.reload_all_tanks_flag, self.kill_monitor_reload_flag, ))
		# make this thread a daemon, meaning that it will exit when all non-daemon threads have exited.
		self.monitor_reload_flag.daemon = True
		# start monitoring
		self.monitor_reload_flag.start()

	def read_protocol(self):
		try:
			# try to open the configuration file, and try to load devices and tanks
			self.config.read(self.config_filename)

			if not self.config.has_section(self.id):
				raise errors.FatalConfigError("No settings found for this device (" + self.id + ").")
			else:
				self.load_devices()
				self.load_tanks()
		except errors.FatalConfigError as ce:
			p("\n\t!!!\t")
			p(  "\t!!!\tConfiguration File Error: " + str(ce))
			p(  "\t!!!\tAborting")
			p(  "\t!!!\t\n")
			raise errors.FatalError

	# look for skinnerbox modules on serial ports that are not currently open
	# open and store them in self.deviceList
	def load_devices(self):
		p("\nChecking devices")
		p(  "################")
		# list the ports found in the file system ("/dev/ttyUSB*")
		portList = glob.glob('/dev/ttyUSB*')
		numPorts = len(portList)
		p("Found " + str(numPorts) + " ports:")
		for d in portList:
			p("\t" + d)
		
		# see whether an attached device is a skinner box module and if so save it in the deviceList
		def connect_device(d):
			# if the device is already in the list, see whether it is open. if so, return.
			if d in self.deviceList:
				if self.deviceList[d].con.is_open:
					p("device " + d + " is already open.")
					return
			# if the device is not in the list or has been closed, try to open it
			dev = skinnerbox.device.connect_device(d)
			if not dev:
				p(d + " not recognized as skinnerbox module.")
				return
			dev_id = dev.pid()
			self.deviceList[d] = dev
			return

		# try to connect all ports
		# this is done in a separate thread for each port to save time
		t = [] # a list of threads to be started and then waited for
		for d in portList:
			t.append(threading.Thread(name = d + "_connection_thread", target = connect_device,  args=(d,)))
			t[-1].start() # start a thread to check each device
		for i in t:
			i.join() # wait for all devices to be checked before continuing (see threading.join)

		# remove devices that are no longer connected from the list
		devicesToRemove = []
		for d in self.deviceList:
			if not self.deviceList[d].con.is_open:
				p(self.deviceList[d].pid() + " at " + d + " no longer found. removing it from the list.")
				devicesToRemove.append(d)
		for d in devicesToRemove:
			del self.deviceList[d]

		# print the elements of the given module list
		numDevFound = len(self.deviceList)
		p("Found " + str(numDevFound) + " modules:")
		for d in self.deviceList:
			p("\t" + self.deviceList[d].pid() + " at " + d)

		# the remainder of this method is concerned with uploading new firmware versions. this should be done differently and more user-friendly in the future.
		#  for the moment, set the flag and provide the file to upload new firmware to all attached devices.
		upload_feeder_code       = False
		upload_button_code       = False
		if upload_feeder_code or upload_button_code:
			button_firmware_loc      = self.basedir + '/button.hex'
			feeder_firmware_loc      = self.basedir + '/feeder.hex'
			if 'PI_' in self.id:
				avrdude_bin_loc  = '/usr/bin/avrdude'
				avrdude_conf_loc = '/etc/avrdude.conf'
			elif self.id == 'Laptop':
				avrdude_bin_loc  = '/home/jan/Downloads/arduino-1.8.9-linux64/arduino-1.8.9/hardware/tools/avr/bin/avrdude'
				avrdude_conf_loc = '/home/jan/Downloads/arduino-1.8.9-linux64/arduino-1.8.9/hardware/tools/avr/etc/avrdude.conf'
			else:
				p("cannot upload: no directory information found for this device (" + self.id)

			for d in self.deviceList:
				if 'FEEDER' in self.deviceList[d].pid():
					if upload_feeder_code:
						p("uploading code to " + self.deviceList[d].pid())
						os.system(avrdude_bin_loc + ' -C' + avrdude_conf_loc + ' -v -patmega328p -carduino -P' + d + ' -b57600 -D -Uflash:w:' + feeder_firmware_loc + ':i')
						p("done with " + self.deviceList[d].pid())
				if 'BUTTON' in self.deviceList[d].pid():
					if upload_button_code:
						p("uploading code to " + self.deviceList[d].pid())
						os.system(avrdude_bin_loc + ' -C' + avrdude_conf_loc + ' -v -patmega328p -carduino -P' + d + ' -b57600 -D -Uflash:w:' + button_firmware_loc + ':i')
						p("done with " + self.deviceList[d].pid())

	# look for tanks that are not currently loaded
	# load them and store them in self.tankList, which is a dictionary that maps tank names to tank instances
	def load_tanks(self):
		p("\nChecking Tanks")
		p(  "##############")
		# see which of the tanks specified in the protocol are to be controled by this device
		# tankListGiven will store the NAMES of these tanks
		tankListGiven = []
		sections      = self.config.sections()
		for s in sections:
			if 'Tank' in s:
				if self.config.get(s, "controler") == self.id:
					tankListGiven.append(s)
		numTanks = len(tankListGiven)
		if numTanks == 0:
			raise errors.FatalConfigError("No Tanks to be conrtolled by this device (" + self.id + ").")
		else:
			p("found " + str(numTanks) + " Tanks:")
			for t in tankListGiven:
				p("\t" + t)

		# load the tanks, if they are not already loaded (this may be the case if load_tanks is called to reload only one tank)
		for t in tankListGiven:
			if not t in self.tankList:
				try:
					self.tankList[t] = skinnerbox_games.tank.load_tank(self.config, t, self.deviceList)
				except errors.MinorConfigError as ce:
					p("\n\t!!!\t")
					p(  "\t!!!\tError when loading " + t + ": " + str(ce))
					p(  "\t!!!\t\n")

		if len(self.tankList) == 0:
			raise errors.FatalConfigError("Could not load any of the tanks.")

	def run(self):
		# for each tank, create some dictionary entries, with the tanks name as the key:
		# the name of a file that serves as a reload flag (when the file is modified, the tank will reload)
		# the file with this name
		# a thread monitoring changes in this file
		# an item in the itc dictionary with an event that is set by this monitoring thread in case the file is modified
		# an event that, if set, causes the monitor thread to return
		self.reload_tank_flag_filenames = {}
		self.reload_tank_files          = {}
		self.monitor_threads            = {}
		self.monitor_thread_kill_flags  = {}
		for t in self.tankList:
			self.reload_tank_flag_filenames[t] = self.basedir + "/reload_flag_" + t + ".txt"
			self.reload_tank_files[t]          = open(self.reload_tank_flag_filenames[t], 'w+')
			self.reload_tank_files[t].close()
			self.itc.reload_tank_flags[t]    = threading.Event()
			self.monitor_thread_kill_flags[t]  = threading.Event()
			self.monitor_threads[t]            = threading.Thread(name = t + "_relaod_flag_monitor", target = detect_file_modification, args = (self.reload_tank_flag_filenames[t], self.itc.reload_tank_flags[t], self.monitor_thread_kill_flags[t], ))
			self.monitor_threads[t].daemon     = True			
			self.monitor_threads[t].start()

		# for each tank, create a separate thread that runs that tank and store it in a dictionnary with the tanks name as key
		tank_threads = {}
		for t in self.tankList:
			tank_threads[t] = threading.Thread(name = t + "_running_thread", target = self.tankList[t].run)
			tank_threads[t].start()

		# reload or stop tanks forever
		while 1:
			# if all tanks have to be stopped
			if self.itc.stop_all_tanks_flag.isSet():
				for t in tank_threads:
					tank_threads[t].join()
					return
				
			# if all tanks have to be reloaded
			if self.itc.reload_all_tanks_flag.isSet():
				# wait for all tanks to return and remove them from the tankList dictionary with del
				# tanks will stop by themselves if this flag is set
				p("waiting for all tanks to return...")
				for t in tank_threads:
					tank_threads[t].join()
					p("deleting tank " + t)
					del self.tankList[t]
					p("ok.")
				p("ok. clearing reload all tanks flag...")
				# clear the flag that caused this execution
				self.itc.reload_all_tanks_flag.clear()
				p("ok. reading protocol...")
				# reload the protocol, which will reload the tanks
				self.read_protocol()
				# restart all tanks
				for t in self.tankList:
					tank_threads[t] = threading.Thread(name = t + "_running_thread", target = self.tankList[t].run)
					tank_threads[t].start()
			# if a specific tank has to be reloaded
			for t in self.itc.reload_tank_flags:
				if self.itc.reload_tank_flags[t].isSet():
					# wait for this tank to return
					tank_threads[t].join()
					p("tank has returned")
					# clear the flag that caused this execution
					self.itc.reload_tank_flags[t].clear()
					# remove the tank from the list, so that read_protocol will reload it
					del self.tankList[t]
					self.read_protocol()
					# restart the tank
					tank_threads[t] = threading.Thread(name = t + "_running_thread", target = self.tankList[t].run)
					tank_threads[t].start()


	def close_devices(self):
		for m in self.moduleListFound:
			m.close_device()
		
	def reset_protocol(self):
		self.close_devices()
		self.read_protocol()
		self.reload_protocol.clear()


