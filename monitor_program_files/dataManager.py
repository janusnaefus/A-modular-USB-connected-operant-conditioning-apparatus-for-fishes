import dataGrabber
import skinnerboxFiles as sf


import os
import pandas as pd
import numpy  as np
import ConfigParser
import json

# a function to "touch" files, i.e. change their last modification date (or create them if they do not exist)
# this is used on flag files ont he network folder, whose modification date is monitored by the controllers, e.g. to reload a tank or the entire code.
def touch(fname):
	open(fname, 'wa').close() 

# DataManager produces summary tables of the data collected by DataGrabber
class DataManager:
	def __init__(self):
		self.dg = dataGrabber.DataGrabber()

		if os.path.isfile(sf.config_filename):
			print "found config file\n"
			self.config = ConfigParser.ConfigParser()
			self.config.read(sf.config_filename)
		else:
			print "Error: config file not found\n"

	def get_data(self):
		return self.data

	def update(self):
		# see whether there is new data and if so, create summaries for it
		return self.dg.update()

	def schedule_progression(self):
		exclude_fish = json.loads(self.config.get("exclude_from_schedule_progression", "fish_list"))
		for i, row in self.summary_data.iterrows():
			if not row['fish'] in exclude_fish:
				s = row['schedule']
				for o in self.config.options("schedule_progression"):
					if o == s:
						if row['ntrials'] >= 10:
							if row['median'] < 60:
								print row['fish'] + ': ' + o + ' >> ' + self.config.get("schedule_progression", o)
								self.change_schedule(row['tank'], self.config.get("schedule_progression", o))

	def change_schedule(self, t, s):

		print t
		
		with open(sf.config_filename, 'r') as f:
			rawData  = f.readlines()

		found_tank = False
		for i, line in enumerate(rawData):
			#print line
			if not found_tank and line.startswith('[' + t):
				found_tank = True
				continue
			if found_tank and line.startswith('['):
				print "could not change schedule: line not found"
				break
			if found_tank and line.startswith('schedule:'):
				print "changing schedule..."
				rawData[i] = "schedule: " + s + "\n"
				break

		with open(sf.config_filename, 'w') as f:
			for i, l in enumerate(rawData):
				f.write(l)


		self.config.read(sf.config_filename)
		
		touch(sf.remote_data_folder + 'reload_flag_' + t + '.txt')
				
				
			#schedule              = [ line for i, line in enumerate(rawData) if line.startswith('[schedule') ][0]


	def make_summaries(self, fish):
		# get the data from datagrabber
		self.data     = self.dg.getdata()
		self.metadata = self.dg.getmetadata()
		# make three summary tables
		self.make_currently_playing_fish_summary()
		self.make_individual_fish_summary(fish)
		self.make_all_trials_summary()
			
	def make_currently_playing_fish_summary(self):
		# get a list of fish who are currently playing
		tank_list          = []
		fish_list          = []
		schedule_list      = []
		module_list        = []

		# look in the training protocol which fish are currently playing
		sections      = self.config.sections()
		#for s in sections:
		#	if 'Tank' in s:
		#		if self.config.get(s, 'controler') != 'None':
		#			tank_list.append(s)
		#			fish_list.append(self.config.get(s, 'fishList'))
		#			schedule_list.append(self.config.get(s, 'schedule'))
		#			module_list.append(self.config.get(s, 'moduleList'))

		for s in sections:
			if 'Tank' in s:
				if self.config.get(s, 'controler') != 'None':
					fl = json.loads(self.config.get(s, "fishList"))
					ml = json.loads(self.config.get(s, "moduleList"))
					for i, f in enumerate(fl):
						fish_list.append(f)
						tank_list.append(s)
						schedule_list.append(self.config.get(s, 'schedule'))
						module_list.append(ml[i*2] + ', ' + ml[i*2+1])

		# remove the trailing and leading [" from the fish list to get the blank fish names
		#fish_list     = [f[2:-2] for f in fish_list]
		
		# store information on all fish in a data frame
		df = pd.DataFrame({'fish': fish_list, 'tank': tank_list, 'schedule': schedule_list, 'modules': module_list})
		df['bstate']  = "na"
		df['ntrials'] = 0
		df['fstate']  = "na"
		df['median']  = "na"
		df['lasterror']  = "na"
		df['lasttrial']  = "na"

		df = df[['fish', 'tank', 'schedule', 'bstate', 'ntrials', 'modules']]
		
		for i, row in df.iterrows():
			# get the last data line for the current fish
			temp = self.data
			temp = temp.loc[temp['fish'] == row['fish']]

			#temp = temp[temp['schedule'] == row['schedule']]
			
			if len(temp) > 0:
				temp = temp[temp['time'] == max(temp['time'])]

			if len(temp) > 0:
				df.loc[df.index[i], 'lasttrial'] = temp['time'].iloc[0].strftime('%d.%m %H:%M')
			else:
				df.loc[df.index[i], 'lasttrial'] = pd.NaT

			# determine in which state the button is currently in
			if len(temp) > 0:
				if temp['triggered'].iloc[0]:
					df.loc[df.index[i], 'bstate'] = "Triggered"
				elif not pd.isnull(temp['disarmedLine'].iloc[0]):
					df.loc[df.index[i], 'bstate'] = "Disarmed"
				elif temp['comments'].iloc[0] == "stop_time_is_up":
					df.loc[df.index[i], 'bstate'] = "Time out"
				else:
					df.loc[df.index[i], 'bstate'] = "Armed"

				# if the fish should have been fed but has not received food, indicate this
				if not pd.isnull(temp['fedLine'].iloc[0]) and temp['reward_method'].iloc[0] == "feed" and temp['value2'].iloc[0] == 0:
					df.loc[df.index[i], 'fstate'] = "Clogged"
				else:
					df.loc[df.index[i], 'fstate'] = "OK"

				# see whether there was a device error recently
				if str(temp['comments'].iloc[0]).startswith("stop_error"):
					if 'BUTTON' in str(temp['comments'].iloc[0]):
						df.loc[df.index[i], 'bstate'] = "Error"
					if 'FEEDER' in str(temp['comments'].iloc[0]):
						df.loc[df.index[i], 'fstate'] = "Error"
			else:
				df.loc[df.index[i], 'bstate'] = "Unknown"
				df.loc[df.index[i], 'fstate'] = "Unknown"

			# see when the last error occured
			temp = temp.loc[temp['fish'] == row['fish']]
			temp = temp.loc[temp['comments'].notnull()]
			if len(temp) > 0:
				temp = temp.loc[temp['comments'].str.startswith('stop_error', na = False)]
			if len(temp) > 0:
				temp = temp[temp['time'] == max(temp['time'])]
				df.loc[df.index[i], 'lasterror'] = temp['time'].iloc[0].strftime('%d.%m %H:%M')

			# see how many trials the fish has played of the current schedule
			temp = self.data
			temp = temp.loc[temp['fish'] == row['fish']]
			temp = temp[temp['schedule'] == row['schedule']]
			v    = len(temp)
			df.loc[df.index[i], 'ntrials'] = len(temp)

			# calculate the median trigger delay over the last 10 successful trials
			temp = temp[-10:]
			# if there are no values, the median will be nan and round will throw an error.
			if len(temp):
				df.loc[df.index[i], 'median'] = temp['trigger_delay'].median().round(2)
			else:
				df.loc[df.index[i], 'median'] = temp['trigger_delay'].median()
		
		# copy the data frame for other summary functions to work with
		self.summary_data = df.copy()

		# make the data pritty for displaying
		df['tank']     = [t.replace('Tank ', '') for t in df['tank']]
		df['schedule'] = [s.replace('schedule ', '') for s in df['schedule']]
		#df['modules']  = [m.replace('["', '') for m in df['modules']]
		#df['modules']  = [m.replace('"]', '') for m in df['modules']]
		#df['modules']  = [m.replace('"', '') for m in df['modules']]
		
		self.cps = df

		
	def make_individual_fish_summary(self, fish):
		f  = fish
		sd = self.summary_data

		if f is None:
			f = sd['fish'].iloc[0]

		fd = {}
		fd['fish'] = f
		fd['schedule'] = sd.loc[sd['fish'] == f, 'schedule'].iloc[0]
		temp = self.data
		temp = temp[temp['fish'] == fd['fish']]
		temp = temp[temp['schedule'] == fd['schedule']]
		if len(temp):
			v = 100 * float(len(temp[temp['triggered'] == True])) / float(len(temp))
		else:
			v = 0
		fd['Percent pushed'] = str(round(v, 3)) + '%'
		
		
		df = pd.DataFrame.from_dict(fd, orient = 'index', columns = ['value'])
		df['index'] = df.index
		df = df[['index', 'value']]
		df.index = range(0,len(df))

		self.ifs = df

	def make_all_trials_summary(self):
		d  = self.data
		sd = self.summary_data

		ad = {}
		ad['total trials'] = len(d)
		ad['total fish']   = len(d['fish'].unique())

		df = pd.DataFrame.from_dict(ad, orient = 'index', columns = ['value'])
		df['index'] = df.index
		df = df[['index', 'value']]
		df.index = range(0,len(df))
	
		self.ats = df
