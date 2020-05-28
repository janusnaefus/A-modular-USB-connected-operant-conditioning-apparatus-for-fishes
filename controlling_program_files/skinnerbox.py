import serial
import time
import random
import threading
import skinnerbox_errors as errors
import skinnerbox_interThreadCommunication as interThreadCom

# these parameters should also be read from a config filess
randomize_order = True
rough_callibration = True

def trim_eol(s):
	# trims the two end of line characters "\r\n" from a given string s
	if s.endswith("\r\n"):
		return s[:-2]
	else:
		return s

def map_range_int(value, fromMin, fromMax, toMin, toMax):

	# Figure out how 'wide' each range is
	fromSpan = fromMax - fromMin
	toSpan   = toMax   - toMin

	# Convert the left range into a 0-1 range (float)
	valueScaled = float(value - fromMin) / float(fromSpan)
	valueScaled = int(valueScaled * toSpan)

	# Convert the 0-1 range into a value in the right range.
	return valueScaled

class device:
	@staticmethod
	def connect_device(port):
		# open the port
		# see whether the attached device is a valid device
		# if so, determine the id
		# depending on the id, return a feeder, a button or a scale, or close the connection
		
		def open_port(port):
			try:
				con = serial.Serial(port=port,
							baudrate=9600,
							parity=serial.PARITY_NONE,
							stopbits=serial.STOPBITS_ONE,
							bytesize=serial.EIGHTBITS, 
							timeout=0)
			except:
				print "port " + port + " cannot be opened."
				return 0
			return con
			
		def test_con(con):
			dev = device(con,  None)
			if not dev.wait_OK():
				return 0
			if dev.get_id():
				return dev.pid()
			else:
				print "no id :("
				return 0
		
		con = open_port(port)
		if not con:
			return 0
		id = test_con(con)
		if not id:
			con.close()
			return 0
		elif 'FEEDER' in id:
			return feeder(con,  id)
		elif 'BUTTON' in id:
			return button(con,  id)
		elif 'SWITCH' in id:
			return switch(con,  id)
		
	def __init__(self,  con,  id):
		self.itc  = interThreadCom.interThreadCom()
		self.lock = threading.Lock()
		self.con = con
		self.ID = id
		
	def get_port(self):
		return self.con.port

	def close_device(self):
		self.lock.acquire()
		self.con.close()
		self.lock.release() 
	
	def purge(self):
		self.lock.acquire()
		self.con.reset_input_buffer()
		self.con.reset_output_buffer()
		self.lock.release()	
		
	def pid(self):
		return(self.ID)

	def get_id(self):
		self.lock.acquire()
		self.con.write("ID")
		if self.wait_OK():
			self.ID = trim_eol(self.con.readline())
			answer =  1
		else:
			answer = 0
		self.lock.release()
		return answer

	def wait_OK(self):
		while True:
			try:
				waiting = self.con.inWaiting()
				if waiting >= 4:
					msg = trim_eol(self.con.readline())
					if msg == "OK":
						return 1
					else:
						return 0
			except:
				self.itc.send_message(self.ID + ": error in wait OK")
				return 0

	def read_answer(self):
		while True:
			try:
				waiting = self.con.inWaiting()
				if waiting >= 1:
					msg = trim_eol(self.con.readline())
					return msg
			except:
				self.itc.send_message(self.ID + ": error in read_answer")
				return 0


class feeder(device):

	def do_nothing(self, value):
		return 0, 0

	# feed feeds and waits until the feeding is done, then returns the amount fed	
	def feed(self, _amount):
		self.lock.acquire()
		try:
			self.con.write("f" + str(_amount))
		except:
			self.itc.send_message(self.ID + ": error in con.write")
		self.wait_OK()
		fed_duration = self.read_answer()
		fed_amount = self.read_answer()
		self.wait_OK()
		self.lock.release()
		return fed_duration, fed_amount
		
	# feed2 starts a thread that feed()s and returns immediately
	def feed2(self, _amount):		
		f = threading.Thread(name = self.ID + '_feeding_thread',  target = self.feed,  args=(_amount,))
		f.start()
		
	def run_trial(self, s,   speed,  duration):
		weight_before = s.read()
		self.feed(duration,  speed)
		time.sleep(5)
		weight_after = s.read()
		result = weight_after - weight_before
		print result
		return weight_after - weight_before

	def test_calibration(self,  calibration_data):
		def test_minimum_speed(calibration_data):
			return 0
		def test_variance(calibration_data):
			return 0
		def test_maximum_amount(calibration_data):
			return 0
			
		passed = False
		passed = test_minimum_speed(calibration_data) and test_variance(calibration_data) and test_maximum_amount(calibration_data)
		return passed
		
	def generate_trials(self):
		trials = []
		if rough_callibration:
			for speed in [1023]:
				for duration in range(0, 1200,  20):
					for trial in range(1, 4):
						trials += [[speed,  duration]]
		else:
			for speed in range(500, 1024, 10):
				for duration in range(0, 600,  20):
					for trial in range(1, 5):
						trials += [[speed,  duration]]
		if randomize_order:
			random.shuffle(trials)			
		return trials

	def calibrate(self,  s,  calibration_file_name):
		f = open(calibration_file_name,  'w')
		trials = self.generate_trials()
		for t in trials:
			weight = self.run_trial(s,  t[0],  t[1])
			t += [weight]
		for t in trials:
			for i in range(0, len(t)):
				f.write(str(t[i]))
				if not i == len(t) - 1:
					f.write(',')
			f.write('\n')
		f.close()
		calibrated = self.test_calibration(trials)
		return calibrated


class button(device):
	def led_on(self, _r, _g, _b):
		def _led_on(_r, _g, _b):
			self.lock.acquire()
			self.con.write("a" + str(_r) + "," + str(_g) + "," + str(_b))
			self.wait_OK()
			self.lock.release()
		
		k = threading.Thread(name = self.ID + '_led_on_thread',  target = _led_on, args=(_r, _g, _b,))
		k.start()
		
	def led_off(self):
		def _led_off():
			self.lock.acquire()
			self.con.write("d")
			self.wait_OK()
			self.lock.release()
		
		k = threading.Thread(name = self.ID + '_led_off_thread',  target = _led_off)
		k.start()
		
	def klick(self, t, e):
		def _klick(t, e):
			self.lock.acquire()
			self.con.write("k" + str(t))
			self.wait_OK()
			self.lock.release()
			e.set()
		
		k = threading.Thread(name = self.ID + '_klicking_thread',  target = _klick,  args=(t, e))
		k.start()
		
	def trig(self):
		waiting = self.con.inWaiting()
		if waiting >= 11:
			msg = trim_eol(self.con.read(11))
			if msg == "TRIGGERED":
				return 1
			else:
				return 0
		else:
			return 0
		
	def set_thr(self,  t):
		self.thr = t
		def _set_thr():
			self.lock.acquire()
			self.con.write("t" + str(self.thr))
			self.wait_OK()
			self.lock.release()
		
		k = threading.Thread(name = self.ID + '_set_thr_thread',  target = _set_thr)
		k.start()

		
	def measure(self,  t):
		values = []
		buffer = ""
		self.lock.acquire()
		self.con.write("r" + str(t))
		self.lock.release()
		time.sleep(t + 1)
		receiving = self.con.inWaiting()
		while receiving > 0:
			buffer += self.con.read(receiving)
			receiving = self.con.inWaiting()
		values = buffer.splitlines()
		if values[0] == "OK" and values [-1] == "OK":
			values = values[1:-1]
			values = map(int,  values)
			return values
		else:
			return None;
		
	def test_calibration(self):
		passed = False
		while 1:
			for i in range(1, 10):
				self.set_thr(i)
				print "try the button! difficulty = " + str(i)
				self.led_on()
				while not self.trig():
					continue
				print "well done!"
				time.sleep(1)
			answer = raw_input("test again?")
			if answer != "y":
				break



class switch(device):		
	def turn_on_for(self, t, e):
		def _turn_on_for(t, e):
			self.lock.acquire()
			self.con.write("o" + str(t))
			self.wait_OK()
			self.lock.release()
			e.set()
		s = threading.Thread(name = self.ID + '_switch_on_for_thread',  target = _turn_on_for,  args=(t, e))
		s.start()

	def turn_off_for(self, t, e):
		def _turn_off_for(t, e):
			self.lock.acquire()
			self.con.write("c" + str(t))
			self.wait_OK()
			self.lock.release()
			e.set()
		s = threading.Thread(name = self.ID + '_switch_off_for_thread',  target = _turn_off_for,  args=(t, e))
		s.start()

	def turn_on(self):
		def _turn_on():
			self.lock.acquire()
			self.con.write("+")
			self.wait_OK()
			self.lock.release()
		s = threading.Thread(name = self.ID + '_switch_on_thread',  target = _turn_on)
		s.start()
		
	def turn_off(self):
		def _turn_off():
			self.lock.acquire()
			self.con.write("-")
			self.wait_OK()
			self.lock.release()
		s = threading.Thread(name = self.ID + '_switch_off_thread',  target = _turn_off)
		s.start()

# this calibrates the feeder by weighing the amount of food it delivers over a range of settings.
# a rough calibration takes 1.5 minutes, if the scale takes 1 second to stabilize.
# a thorough calibration would take 1 hour 45 minutes.
class scale:
	scale_read_command = "READ"
	
	def __init__(self,  port):
		self.con = serial.Serial(port=port,
									baudrate=9600,
									parity=serial.PARITY_NONE,
									stopbits=serial.STOPBITS_ONE,
									bytesize=serial.EIGHTBITS, 
									timeout=0)
	
	def read(self):
		answer = None
		while answer == None:
			buf = ""
			while self.con.inWaiting():
				self.con.read()
			self.con.write('w')
			while True:
				if self.con.inWaiting():
					buf += self.con.read()
					if buf[-1] == 'g':
						buf = buf[-11:-2]
						break
					if buf[-1] == '\n':
						buf = buf[-11:-2]
						break
			try:
				answer = float(str(buf))
			except:
				answer = None
		return answer
		
	def purge(self):
		self.con.reset_input_buffer()
		self.con.reset_output_buffer()		

