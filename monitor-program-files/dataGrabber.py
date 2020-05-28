


import os
import shutil
import pandas as pd
import numpy  as np
import datetime


import skinnerboxFiles as sf


ArmedEventsToReReadInNewFiles = 5

# DataGrabber monitors the skinnerbox output and collects the data as it is produced


class FatalFileError(Exception):
	pass


class DataGrabber:
	def __init__(self):
		print "initializing data grabber\n"
		try:
			self.checkFiles()
			print "done\n"
		except FatalFileError as e:
			print "Error when loading files:\n" + str(e) + "\naborting...\n"
			exit()

	def getdata(self):
		return self.correct_data()

	def getmetadata(self):
		return self.metadata

	def correct_data(self):
		df = self.data.copy()
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Judith'),'fish'] = 'Cynthia_'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Cynthia'),'fish'] = 'Judith'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Cynthia_'),'fish'] = 'Cynthia'

		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Jones'),'fish'] = 'Stephanie_'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Stephanie'),'fish'] = 'Jones'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Stephanie_'),'fish'] = 'Stephanie'
		
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Grace'),'fish'] = 'Erica_'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Erica'),'fish'] = 'Grace'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Erica_'),'fish'] = 'Erica'
		
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Michone'),'fish'] = 'Picola_'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Picola'),'fish'] = 'Michone'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Picola_'),'fish'] = 'Picola'
		
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Giulia'),'fish'] = 'Heidi_'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Heidi'),'fish'] = 'Giulia'
		df.loc[(df.time > datetime.datetime.strptime("20190612_0000", "%Y%m%d_%H%M")) & (df.time < datetime.datetime.strptime("20190625_1430", "%Y%m%d_%H%M")) & (df.fish == 'Heidi_'),'fish'] = 'Heidi'
		return df

	def checkFiles(self):
		# checks whether the required files and folders exist
		print "checking files\n"

		has_local_files  = True
		has_remote_files = True

		# look for the local and remote data folders.
		# if  you cannot find them, throw an error
		# if they both have no files, throw an error
		if os.path.isdir(sf.local_data_folder):
			print "found local data folder\n"
			self.local_data_file_list = os.listdir(sf.local_data_folder)
			self.local_data_file_list = [sf.local_data_folder + f for f in self.local_data_file_list  if f.startswith("Tank ")]
			n_local_files = len(self.local_data_file_list)
			if n_local_files > 0:
				print "found " + str(n_local_files) + " files in the local data folder\n"
			else:
				has_local_files = False
		else:
			raise FatalFileError("local data folder not found")

		if os.path.isdir(sf.remote_data_folder):
			print "found remote data folder\n"
			self.remote_data_file_list = os.listdir(sf.remote_data_folder)
			self.remote_data_file_list = [sf.remote_data_folder + f for f in self.remote_data_file_list  if f.startswith("Tank ")]
			n_remote_files = len(self.remote_data_file_list)
			if n_remote_files > 0:
				print "found " + str(n_remote_files) + " files in the remote data folder\n"
			else:
				has_remote_files = False
		else:
			raise FatalFileError("remote data folder not found")

		if not has_local_files and not has_remote_files:
			raise FatalFileError("no files in remote data folder")

		# look for the data and metadata files.

		has_data_file = True
		has_metadata_file = True

		if os.path.isfile(sf.data_filename):
			print "found data file\n"
			try:
				self.data     = pd.read_csv(sf.data_filename, parse_dates = ['time', 'time_triggered'])
			except pd.errors.EmptyDataError as e:
				print "data file is empty: " + str(e)
				has_data_file = False
		else:
			print "could not find data file\n"
			has_data_file = False

		if os.path.isfile(sf.metadata_filename):
			print "found metadata file\n"
			try:
				self.metadata = pd.read_csv(sf.metadata_filename, parse_dates = ['reading_date'])
			except pd.errors.EmptyDataError as e:
				print "metadata file is empty: " + str(e)
				has_metadata_file = False
		else:
			print "could not find metadata file\n"
			has_metadata_file = False

		# if both files could be loaded, everything is ok. return.
		if has_data_file and has_metadata_file:
			return

		# if one file but not the other has been found (!= is xor in this case), throw an error
		if has_metadata_file != has_data_file:
			raise FatalFileError("found only one of data.csv and metadata.csv - this does not make senes. aborting...")

		# if both do not exist, load the data files (it has been checked whether they exist before)
		else:
			if raw_input("Could not find any compiled data. reload raw data? (y/n)\n") == 'y':
				self.data     = None
				self.metadata = None
				if has_local_files:
					self.reloadLocalData()
				self.update()
			else:
				raise FatalFileError("aborted by user.")


	def loadFiles(self):
		pass


	def update(self):
		data_changed = False
		if self.copyCompleteFiles():
			data_changed = True
		if self.getNewData():
			data_changed = True

		if data_changed:
			self.writeData()
			self.writeMetadata()
			return True
		else:
			return False

	def reloadLocalData(self):
		if len(self.local_data_file_list) > 0:
			self.append_files(self.local_data_file_list)
			self.writeData()
			self.writeMetadata()
		else:
			raise FatalFileError("no local files to reload")

	def append_files(self, file_list):
		data_changed = False
		
		start_time = datetime.datetime.now()

		files_loaded = 0
		n_files      = len(file_list)

		print "loading " + str(n_files) + " files\n"

		for f in file_list:
			percent_loaded = round((float(files_loaded) / float(n_files) * 100), 1)
			print os.path.basename(f)
			print str(files_loaded) + ' of ' + str(n_files) + ' (' + str(percent_loaded) + '%)\n'
			newdata, newmetadata = self.readSkinnerboxFile(f)
			if newdata is not None:
				data_changed = True
				if self.data is not None:
					self.data = pd.concat([self.data, newdata], sort = False)
				else:
					self.data = newdata
			if newmetadata is not None:
				data_changed = True
				if self.metadata is not None:
					self.metadata = pd.concat([self.metadata, newmetadata], sort = False)
				else:
					self.metadata = newmetadata
			files_loaded   = files_loaded + 1

		self.data = self.data.sort_values(by = 'time')
		self.data = self.data.reset_index(drop = True)

		self.metadata = self.metadata.sort_values(by = 'reading_date')
		self.metadata = self.metadata.reset_index(drop = True)

		print "done."
		print 'loaded ' + str(files_loaded) + ' files in ' + str((datetime.datetime.now() - start_time).total_seconds()) + ' seconds.\n'
		
		return data_changed

	def writeData(self):
		# print "writing data to file..."
		with open(sf.data_filename, 'w+') as f:
			f.write(self.data.to_csv(index = False))

	def writeMetadata(self):
		# print "writing metadata to file..."
		with open(sf.metadata_filename, 'w+') as f:
			f.write(self.metadata.to_csv(index = False))

	def copyCompleteFiles(self):
		# in the remote folder, data is only written to the newest file for each tank
		# this function gets completed files, reads them and moves them to the local folder

		file_list    = os.listdir(sf.remote_data_folder)
		file_list    = [f       for f in file_list  if f.startswith("Tank ")]
		# tank and creation data re written in the filename
		tank_list    = [f[5: 8] for f in file_list]
		date_list    = [f[9:31] for f in file_list]
	
		file_list         = pd.DataFrame({'file': file_list, 'tank': tank_list, 'date': date_list})
		file_list['date'] = pd.to_datetime(file_list['date'], format = '%Y%m%d_%H%M%S_%f')

		old_files = None

		# for each tank for which there are files
		for t in np.unique(file_list['tank']):
			# take all files that are of the same tank but older than the newest of these
			f  = file_list.loc[file_list['tank'] == t,].copy()
			of = f.loc[f['date'] < max(f['date']),]

			# if there are any, add them to the old_files list
			if len(of) > 0:
				if old_files is None:
					old_files = of
				else:
					old_files = pd.concat([old_files, of], sort = False)

		# if there are no old files, return
		if old_files is None:
			#print "no old files"
			return 0
		if len(old_files) == 0:
			#print "no old files"
			return 0

		# otherwise, read them. the reading function will check in detail whether the data in the files is really new.
		print "found " + str(len(old_files)) + " old files.\n"
		data_changed = self.append_files([sf.remote_data_folder + f for f in old_files['file']])

		# move them to the data folder
		for i, of in old_files.iterrows():
			print "copying " + of['file'] + " to data folder.\n"
			shutil.copy(sf.remote_data_folder + of['file'], sf.local_data_folder + of['file'])
			print "removing original file\n"
			os.remove(sf.remote_data_folder + of['file'])
			print "done\n"
		
		return data_changed

	def getNewData(self):
		file_list    = os.listdir(sf.remote_data_folder)
		file_list    = [f       for f in file_list  if f.startswith("Tank ")]
		tank_list    = [f[5: 8] for f in file_list]
		date_list    = [f[9:31] for f in file_list]
	
		file_list         = pd.DataFrame({'file': file_list, 'tank': tank_list, 'date': date_list})
		file_list['date'] = pd.to_datetime(file_list['date'], format = '%Y%m%d_%H%M%S_%f')

		new_files = None

		# for each tank, look for the newest files
		for t in np.unique(file_list['tank']):
			f  = file_list.loc[file_list['tank'] == t,].copy()
			nf = f.loc[f['date'] == max(f['date']),]

			# check whether this file has to be read. if so, append it to the file_list
			read_file, from_line, from_armed = self.checkFileStatus(sf.remote_data_folder + nf['file'].iloc[0])
			if read_file:
				if new_files is None:
					new_files = nf
				else:
					new_files = pd.concat([new_files, nf], sort = False)
		
		# if there are no new files, return
		if new_files is None:
			return 0
		if len(new_files) == 0:
			return 0

		# otherwise, read them. the function will return True if it has made any changes to data or metadata
		print "found " + str(len(new_files)) + " new files.\n"


		return self.append_files([sf.remote_data_folder + f for f in new_files['file']])

	def checkFileStatus(self, filename):

		# compares a file to the existing data and metadata. determines if and how much of the file has to be read
		read_file       = None
		from_line       = None
		last_armed_read = None

		# if the metadata is empty, read the file
		if self.metadata is None:
			read_file = True
			from_line = 0
			last_armed_read = 0
		# otherwise
		else:
			# look in the metadata whether the file has been read before
			temp = self.metadata.loc[self.metadata['filename'] == os.path.basename(filename),]
			if len(temp) == 0:
				# if not, read it
				read_file       = True
				from_line       = 0
				last_armed_read = 0
			else:
				# if it is present
				if temp['reading_date'].iloc[0] < datetime.datetime.fromtimestamp(os.path.getmtime(filename)):
					# if it has been modified after the last reading, read only the last few armed events (which might have changed since the last reading)
					read_file = True
					# the last armed event that was read is stored in the metadata for each file
					# substract a certain number to re-read the last rew events.
					# note that this is chosen generously for future compatibility. at the moment, only the last armed event can change.


					last_armed_read = self.metadata.loc[self.metadata['filename'] == os.path.basename(filename), 'last_armed_read'].iloc[0]

					last_armed_read = last_armed_read - ArmedEventsToReReadInNewFiles
					if last_armed_read < 0:
						last_armed_read = 0
						from_line       = 0
					else:
						# get the line in the file where the first armed event to be re-read is located from the data
						temp = self.data
						temp = temp[temp['file']       == os.path.basename(filename)]
						temp = temp[temp['armedIndex'] == last_armed_read]
						from_line = temp['armedLine'].iloc[0]

				# otherwise, do not read the file
				else:
					read_file       = False
					from_line       = None
					last_armed_read = None

		return (read_file, from_line, last_armed_read)

	def readSkinnerboxFile (self, filename):
		read_file, from_line, from_armed = self.checkFileStatus(filename)

		# if the file has to be read and has been read before, remove the corresponding entries from metadata and data
		if read_file:
			if self.metadata is not None:
				# remove the entry in the metadata, if it exists
				self.metadata = self.metadata[self.metadata['filename'] != os.path.basename(filename)]
			if self.data is not None:
				# remove all entries in the data that are of the current file and contain information about the armed events to be re-read
				self.data = self.data[(self.data['file'] != os.path.basename(filename)) | (self.data['armedIndex'] < from_armed)]


		# return None for both data and metadata if the file should not be read
		if not read_file:
			return (None, None)

		file_location   = os.path.dirname(os.path.realpath(filename))
		reading_date    = pd.Timestamp.now()
		last_armed_read = -1

		
		#read the whole file into rawData.
		with open(filename, 'r') as f:
			rawData  = f.readlines()
	
		#find start and end of the data segment
		data_start = [ i for i, line in enumerate(rawData) if line.startswith('[data]') ][0] + 1
		data_end   = len(rawData)
		n_data     = data_end - data_start
			

		# return None for data, but do return the metadata if the file does not contain any data lines
		if n_data == 0:
			data = None
		else:
			#extract the data as a data frame
			data = pd.read_csv(filename, header = 0, skiprows = data_start)

			# if you have to read from a given line on, remove the data up to this line
			data = data.ix[from_line:]

			# get the date the file was created from the independent variables section
			filedate = [ line for i, line in enumerate(rawData) if line.startswith('date:') ][0]
			filedate = filedate[6:-1]
			filedate = datetime.datetime.strptime(filedate, "%Y%m%d_%H%M%S_%f")
			if filedate < datetime.datetime.strptime("20190412", "%Y%m%d"):
				data['task']   = data['tank'] #this column was wrongly labelled in the python code: row "tank" actually contains "task", "tank" was not logged
				data['tank']   = filename[-35:-27]
				data['value1'] = np.nan
				data['value2'] = np.nan
			if filedate < datetime.datetime.strptime("20190417_1730", "%Y%m%d_%H%M"):
				data['delay_after_last_unsuccessful_trial'] = data['delay_after_last_trial']
				data['delay_after_last_successful_trial']   = data['delay_after_last_trial']
				data['override_max_time']                   = 0
				data.drop(columns="delay_after_last_trial", inplace = True)

			schedule              = [ line for i, line in enumerate(rawData) if line.startswith('[schedule') ][0]
			schedule              = schedule[1:-2]
			data['schedule']      = schedule
			data['time']          = pd.to_datetime(data['time'], format = '%Y%m%d_%H%M%S_%f')
			data['dataStartLine'] = data_start

			data                  = self.calculate_trigger_delays(data, from_armed)
		
			if data is not None:
				data['trigger_delay'] = pd.to_numeric(data['trigger_delay'], errors = 'coerce')
				data['value1'] = pd.to_numeric(data['value1'], errors = 'coerce')
				data['value2'] = pd.to_numeric(data['value2'], errors = 'coerce')

				data['file']   = os.path.basename(filename)

				# add the line in the file where this armed event can be found
				data['armedLineAbsolute'] = data['armedLine'] + data_start + 2 # have to add two because data_start is the line number of the header and armedLine starts at 0

				last_armed_read = max(data['armedIndex'])

				# there was a mistake in three fish: the button was outside, but the schedule was set to inside. all parameters were the same, so it is enough to just change shcedule and task.
				data.loc[(data['fish'].isin(["Erica", "Sophie", "Alberta"])) & (data['time'] > datetime.datetime.strptime("20190510_1300", "%Y%m%d_%H%M")) & (data['time'] < datetime.datetime.strptime("20190513", "%Y%m%d")), 'task']     = "task outside_training_phase_1_190408"
				data.loc[(data['fish'].isin(["Erica", "Sophie", "Alberta"])) & (data['time'] > datetime.datetime.strptime("20190510_1300", "%Y%m%d_%H%M")) & (data['time'] < datetime.datetime.strptime("20190513", "%Y%m%d")), 'schedule'] = "schedule outside_training_phase_1_190408"


		# create the metadata for this file
		metadata                 = pd.DataFrame({'filename': os.path.basename(filename), 'reading_date': reading_date, 'last_armed_read': last_armed_read, 'file_location': file_location}, index = [0])
		metadata['reading_date'] = pd.to_datetime(metadata['reading_date'], unit='s')

		return (data, metadata)

	def calculate_trigger_delays(self, d, last_armed_read):
		# store the index (the line in the data section of the file where a data entry comes from) as a column
		d['dataLine'] = d.index

		# extract only the 'armed' events, and return if there are none
		# the .copy() is necessary to explicitly state that we will work with the copy independently from the original data frame and avoid the "A value is trying to be set on a copy of a slice from a DataFrame" warning.
		d_a  = d.loc[d['event'] == 'armed'].copy()
		if len(d_a) == 0:
			return None

		# create columns for storing the time and delay when the button was triggered
		d_a['triggered']      = np.nan
		d_a['time_triggered'] = np.nan
		d_a['trigger_delay']  = np.nan
		d_a['armedIndex']     = np.nan
		d_a['armedLine']      = np.nan
		d_a['triggerLine']    = np.nan
		d_a['fedLine']        = np.nan
		d_a['disarmedLine']   = np.nan
		d_a['comments']       = np.nan

		# just an index to count armed events that have been read. this is necessary because the index of the data frame with all armed events is still that of the original data frame with all events.
		n_armed_read = last_armed_read

		#loop through these armed events
		for i, a in d_a.iterrows():
			# add to the original data the howmanyeth armed event this is
			d_a.loc[a.name, 'armedIndex']    = n_armed_read
			n_armed_read = n_armed_read + 1

			# add the line in which this armed event was found to the original data
			d_a.loc[a.name, 'armedLine']    = a['dataLine']

			# from the original data frame, extract the rows that are about the same fish
			n_a = d.loc[d['fish'] == a['fish']]
			# and have been written later
			n_a = n_a.loc[n_a['dataLine'] > a['dataLine'],]

			# if there is at leat one
			if len(n_a) > 0:
				# take the first one
				n = n_a.iloc[0]
				# if this is a "triggered" event
				if n['event'] == 'triggered':
					# mention that the button was not triggered
					d_a.loc[a.name, 'triggered'] = True					
					# add the time triggered to the current armed event and calculate the trigger delay
					d_a.loc[a.name, 'time_triggered'] = n['time']
					d_a.loc[a.name, 'trigger_delay']  = (d_a.loc[a.name, 'time_triggered'] - d_a.loc[a.name, 'time']).total_seconds()
					# add the line in which the triggered event was found
					d_a.loc[a.name, 'triggerLine']    = n['dataLine']
		
					# if there are at least two
					if len(n_a) > 1:
						# take the second one
						n = n_a.iloc[1]
						# if this is a "fed" event
						if n['event'] == 'fed':
							# add the feeding delay and amount to the current "armed event"
							d_a.loc[a.name, 'value1']  = n['value1']
							d_a.loc[a.name, 'value2']  = n['value2']
							# add the line in which the fed event was found
							d_a.loc[a.name, 'fedLine'] = n['dataLine']

				# if this is a "disarmed" event
				elif n['event'] == 'disarmed':
					# mention that the button was not triggered
					d_a.loc[a.name, 'triggered'] = False
					# set the trigger delay to the button active duration
					d_a.loc[a.name, 'trigger_delay']  = (datetime.datetime.strptime(d_a.loc[a.name, 'button_active_duration'], '%H:%M:%S') - datetime.datetime.strptime('00', '%S')).total_seconds()
					# add the line in which the disarmed event was found
					d_a.loc[a.name, 'disarmedLine']   = n['dataLine']
					
				# if this is another event
				else:
					# mention that the button was not triggered
					d_a.loc[a.name, 'triggered'] = False
					# store the time the fish had the opportunity to push the button in trigger_delay
					d_a.loc[a.name, 'time_triggered'] = n['time']
					d_a.loc[a.name, 'trigger_delay']  = (d_a.loc[a.name, 'time_triggered'] - d_a.loc[a.name, 'time']).total_seconds()
					# write to the comments section which type of event it is. if it is an error, the error message is stored in value1
					d_a.loc[a.name, 'comments']   = str(n['event']) + ' ' + str(n['value1'])

			else:
				# mention that the button was not triggered
				d_a.loc[a.name, 'triggered'] = False
				d_a.loc[a.name, 'comments']  = 'aborted or ongoing'

		return d_a
