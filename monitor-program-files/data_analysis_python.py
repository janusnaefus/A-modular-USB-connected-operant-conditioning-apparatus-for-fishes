
import skinnerplot
import dataManager
import skinnerboxCommander as sbc


import pandas as pd
import datetime
#from datetime import timedelta
#import time
#import os
#import sys
#import shutil
#import random

from tkinter import ttk
from tkinter import *
from tkinter.ttk import *
from tkinter import scrolledtext

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as colors
import matplotlib.cm as cmx

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

#import matplotlib
#matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
#from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

LocalTimeZone = 'Europe/Berlin'


# a function to "touch" files, i.e. change their last modification date (or create them if they do not exist)
# this is used on flag files ont he network folder, whose modification date is monitored by the controllers, e.g. to reload a tank or the entire code.
def touch(fname):
	open(fname, 'wa').close() 





# the main window of the skinnerbox monitor
class App:
	def __init__(self):
		# some fonts
		self.headerfont = 'TkHeadingFont'
		self.cellfont   = 'TkTextFont'

		# initialiye the main window and configure the overall layout
		self.window = Tk()
		self.window.title("SkinnerBox Control")

		self.window.columnconfigure(0, weight=1)
		self.window.rowconfigure(0, weight=1)
		
		self.n = ttk.Notebook(self.window)
		n = self.n

		n.columnconfigure(0, weight=1)
		n.rowconfigure(0, weight=1)	

		w = Frame(n)   # first tab: all fish overview
		self.f2 = Frame(n)   # second tab: single fish view
		self.ctlTab = Frame(n) # third tab: controls
		n.add(w, text='All Fish')
		n.add(self.f2, text='Single Fish')
		n.add(self.ctlTab, text='controls')

		n.grid(row = 0,column = 0)

		w.columnconfigure(0, weight=1)
		w.columnconfigure(1, weight=1)	

		w.rowconfigure(0, weight=0)
		w.rowconfigure(1, weight=1)
		w.rowconfigure(2, weight=1)
		w.rowconfigure(3, weight=1)


		Label(w, text = 'SkinnerBox control', font='TkCaptionFont').grid(row = 0, column = 0, columnspan = 2, sticky = W)


		# subframes:
		self.upf = LabelFrame(w, text = 'controls') # update indicator: just a labelled canvas that changes color when the datagrabber is getting new data
		self.cpf = LabelFrame(w, text = 'Currently playing fish') # currently playing fish: a table of all fish currently running trials
		self.atf = LabelFrame(w, text = 'All trials') # all trials frame: a dictionary display for summary data accross all trials
		self.cfd = LabelFrame(w, text = 'Current fish') # current fish display: shows data about a selected fish
		self.grf = LabelFrame(self.f2, text = 'Individual Fish')

		self.rstFrame = LabelFrame(self.ctlTab, text = 'Reset controllers')
		
		# configure the layout of the frames and subframes
		self.upf.grid(row = 1, column = 0, columnspan = 10, sticky = W + N)
		self.upf.grid_columnconfigure(0, weight=1)
		self.upf.grid_columnconfigure(1, weight=1)
		self.upf.grid_rowconfigure(0, weight=1)
		self.upf.grid_rowconfigure(1, weight=1)

		self.cpf.grid(row = 2, column = 1, sticky = W + N)
		for i in range(0, 21):
			self.cpf.grid_rowconfigure(i, weight=1)
		for i in range(0, 4):
			self.cpf.grid_columnconfigure(i, weight=1)

		self.atf.grid(row = 2, column = 0, sticky = W + N)
		for i in range(0, 10):
			self.atf.grid_rowconfigure(i, weight=1)
		for i in range(0, 2):
			self.atf.grid_columnconfigure(i, weight=1)

		self.cfd.grid(row = 2, column = 2, sticky = W + N)
		for i in range(0, 10):
			self.cfd.grid_rowconfigure(i, weight=1)
		for i in range(0, 2):
			self.cfd.grid_columnconfigure(i, weight=1)

		self.grf.grid(row = 0, column = 0)

		self.rstFrame.grid(row=0, column=0)




		# create update indicator label and indicator light
		Label(self.upf, text = 'Loading').grid(row = 0, column = 0, sticky = W)
		self.upind = Canvas(self.upf, bg = 'grey', width = 20, height= 20)
		self.upind.grid(row = 0, column = 1, sticky = E)

		# create buttons on update indicator
		Button(self.upf, text = 'Show Graph',   command = self.show_graph_callback).grid(row = 1, column = 0, sticky = W)

		# create button on conrtol tab
		Button(self.rstFrame, text = 'Reset Laptop', command = self.reset_laptop_button_callback).grid(row = 0, column = 0, sticky = W)
		Button(self.rstFrame, text = 'Reset PI_001', command = self.reset_pi_001_button_callback).grid(row = 1, column = 0, sticky = W)
		Button(self.rstFrame, text = 'Reset PI_002', command = self.reset_pi_002_button_callback).grid(row = 2, column = 0, sticky = W)
		Button(self.rstFrame, text = 'Reset PI_003', command = self.reset_pi_003_button_callback).grid(row = 3, column = 0, sticky = W)
		Button(self.rstFrame, text = 'Reset All',    command = self.reset_all_button_callback).grid(row = 4, column = 0, sticky = W)

		# an area to draw the graphics to
		self.grf_canvas = Frame(self.grf, border=10, relief=SUNKEN)
		self.grf_canvas.grid(row = 1, column = 0, columnspan = 3)

		# make a title for the graphics frame (the name of the fish)
		self.grf_title = Label(master = self.grf, text = "")
		self.grf_title.grid(row = 2, column = 1)

		# create buttons on graphics frame
		Button(master=self.grf, text='<<', command=self.previous_fish).grid(row = 2, column = 0)
		Button(master=self.grf, text='>>', command=self.next_fish).grid(row = 2, column = 2)
		Button(master=self.grf, text='show schedules', command=self.show_schedules).grid(row = 3, column = 2)
		Button(master=self.grf, text='show dates', command=self.show_dates).grid(row = 4, column = 2)
		Button(master=self.grf, text='clear selection', command=self.clear_selection).grid(row = 5, column = 2)

		self.schedList = Listbox(self.grf, selectmode = MULTIPLE, width = 40)
		self.schedList.grid(row = 3, column = 0, rowspan = 3, sticky = W)
		self.dateList = Listbox(self.grf, selectmode = MULTIPLE, width = 30)
		self.dateList.grid(row = 3, column = 1, rowspan = 3, sticky = W)

		# create the data grabber. the member function passed will display a string on the output widget.
		self.dm = dataManager.DataManager()

		self.skp = skinnerplot.skinnerplot()

	def show_graph_callback(self):

		# remove old graphic
		for widget in self.grf_canvas.winfo_children():
			widget.destroy()

		# prepare the data
		d = self.dm.get_data()


		d = d[d.fish == self.current_fish].copy()
		uniq = list(set(d.schedule))

		z = range(1,len(uniq))

		hot = plt.get_cmap('hot')
		cNorm  = colors.Normalize(vmin=0, vmax=len(uniq))
		scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=hot)

		d['color'] = d.schedule.astype('category')
		d['color_code'] = d.color.cat.codes
		d['rgba_code'] = [scalarMap.to_rgba(x) for x in d.color_code]

		# update the schedule selector
		self.schedList.delete(0, END)
		for s in d.schedule.unique():
			self.schedList.insert(END, s)

		try:
			for i in self.schedSelect:
				ind = 0
				for j in self.schedList.get(0, END):
					if i == j:
						self.schedList.selection_set(ind)
						self.schedList.see(ind)
						self.schedList.activate(ind)
						self.schedList.activate(ind)
					ind += 1
			if len(self.schedList.curselection()):
				d = d[d.schedule.isin(self.schedSelect)]
		except AttributeError:
			pass



		# update the date selector
		d['datestr'] = d.time.dt.strftime('%Y-%m-%d')
		self.dateList.delete(0, END)
		for s in d.datestr.unique():
			self.dateList.insert(END, s)

		try:
			for i in self.dateSelect:
				ind = 0
				for j in self.dateList.get(0, END):
					if i == j:
						self.dateList.selection_set(ind)
						self.dateList.see(ind)
						self.dateList.activate(ind)
						self.dateList.activate(ind)
					ind += 1
			if len(self.dateList.curselection()):
				d = d[d.datestr.isin(self.dateSelect)]
		except AttributeError:
			pass

		# put the focus on the second tab
		self.n.select(self.f2)

		# write the name of the fish
		self.grf_title.configure(text = self.current_fish)

		# draw the plot
		fig = self.skp.draw(d)
		canvas = FigureCanvasTkAgg(fig, master=self.grf_canvas)
		canvas.show()
		canvas.get_tk_widget().grid(row = 1, column = 0, columnspan = 2)

	def clear_selection(self):
		self.schedSelect = ""
		self.dateSelect = ""
		self.show_graph_callback()

	def show_schedules(self):
		self.schedSelect = [self.schedList.get(x) for x in self.schedList.curselection()]
		self.show_graph_callback()

	def show_dates(self):
		self.dateSelect = [self.dateList.get(x) for x in self.dateList.curselection()]
		self.show_graph_callback()

	def next_fish(self):
		for i, row in self.cps_data.iterrows():
			if row.fish == self.current_fish:
				if i < len(self.cps_data)-1:
					self.current_fish = self.cps_data.iloc[i+1].fish
				else:
					print "no next fish"
				break

		self.dm.make_individual_fish_summary(self.current_fish)
		self.display_ifs()
		self.show_graph_callback()

	def previous_fish(self):
		for i, row in self.cps_data.iterrows():
			if row.fish == self.current_fish:
				if i >1:
					self.current_fish = self.cps_data.iloc[i-1].fish
				else:
					print "no previous fish"
				break

		self.dm.make_individual_fish_summary(self.current_fish)
		self.display_ifs()
		self.show_graph_callback()

	def change_fish(self, e):
		try:
			self.currently_highlighted.configure(background = self.window['background'])
		except AttributeError:
			pass
		self.currently_highlighted = e.widget
		e.widget.configure(background = 'yellow')
		self.current_fish = e.widget['text']
		self.window.update()
		self.dm.make_individual_fish_summary(self.current_fish)
		self.display_ifs()

	def reset_laptop_button_callback(self):
		print "resetting the python code for Laptop"
		touch(sbc.reset_laptop_flag_filename)

	def reset_pi_001_button_callback(self):
		print "resetting the python code for PI_001"
		touch(sbc.reset_pi_001_flag_filename)

	def reset_pi_002_button_callback(self):
		print "resetting the python code for PI_002"
		touch(sbc.reset_pi_002_flag_filename)

	def reset_pi_003_button_callback(self):
		print "resetting the python code for PI_003"
		touch(sbc.reset_pi_003_flag_filename)

	def reset_all_button_callback(self):
		print "resetting the python code for All devices"
		touch(sbc.reset_all_flag_filename)

	def run(self):
		self.current_fish = None
		self.dm.make_summaries(self.current_fish)
		self.dm.schedule_progression()
		self.display_all()
		self.update_data()
		self.window.mainloop()

	def update_data(self):
		# see whether there is new data and if so, display it. while this is ongoing, set the update indicator to red
		self.indicate_update('red')

		data_changed = self.dm.update()

		if data_changed:
			self.dm.make_summaries(self.current_fish)
			self.dm.schedule_progression()

			self.display_all()

		self.indicate_update('grey')
		# repeat every second
		self.window.after(1000, self.update_data)

	def display_all(self):
		self.display_ats()
		self.display_ifs()
		self.display_cps()
		self.window.update()

	def display_ats(self, highlight = 'rows'):
		df         = self.dm.ats
		frame      = self.atf
		nrow, ncol = df.shape

		redraw_table = False

		# see whether there a table has been displayed before
		try:
			if self.atf_nrow != nrow or self.atf_ncol != ncol:
				redraw_table = True				
		except AttributeError:
			redraw_table = True

		if redraw_table:
			# remove old labels
			for widget in frame.winfo_children():
				widget.destroy()

			self.atf_widgets = {}

			for col in range(ncol):
				#colwidth = [max(len(str(r)) for r in df.iloc[:,col])]
				for row in range(nrow):
					if col == 0:
						f = self.headerfont
					else:
						f = self.cellfont
					l = Label(frame, text=str(df.iloc[row, col]), anchor = W, font = f)#, width = colwidth)
					l.grid(row=row, column=col, sticky = W, padx = (10,10))
					self.atf_widgets[(row, col)] = l
			self.window.update()

		else:
			for col in range(ncol):
				#colwidth = [max(len(str(r)) for r in df.iloc[:,col])]
				for row in range(nrow):
					if df.iloc[row, col] != self.atf_data.iloc[row, col]:
						self.atf_widgets[(row, col)].configure(text = df.iloc[row, col])
			self.window.update()

		self.atf_data = df
		self.atf_nrow = nrow
		self.atf_ncol = ncol

	def display_ifs(self, highlight = 'rows'):
		df         = self.dm.ifs
		frame      = self.cfd
		nrow, ncol = df.shape

		redraw_table = False

		# see whether there a table has been displayed before
		try:
			if self.ifs_nrow != nrow or self.ifs_ncol != ncol:
				redraw_table = True				
		except AttributeError:
			redraw_table = True

		if redraw_table:
			# remove old labels
			for widget in frame.winfo_children():
				widget.destroy()

			self.ifs_widgets = {}

			for col in range(ncol):
				#colwidth = [max(len(str(r)) for r in df.iloc[:,col])]
				for row in range(nrow):
					if col == 0:
						f = self.headerfont
					else:
						f = self.cellfont
					l = Label(frame, text=str(df.iloc[row, col]), anchor = W, font = f)#, width = colwidth)
					l.grid(row=row, column=col, sticky = W, padx = (10,10))
					self.ifs_widgets[(row, col)] = l
			self.window.update()

		else:
			for col in range(ncol):
				#colwidth = [max(len(str(r)) for r in df.iloc[:,col])]
				for row in range(nrow):
					if df.iloc[row, col] != self.ifs_data.iloc[row, col]:
						self.ifs_widgets[(row, col)].configure(text = df.iloc[row, col])
			self.window.update()

		self.ifs_data = df
		self.ifs_nrow = nrow
		self.ifs_ncol = ncol

	def display_cps(self, highlight = 'columns'):
		df         = self.dm.cps
		df.index = df.index + 1
		df.loc[0] = pd.Series(df.columns.values.tolist(), index=df.columns)
		df = df.sort_index()

		frame      = self.cpf
		nrow, ncol = df.shape


		redraw_table = False

		# see whether there a table has been displayed before
		try:
			if self.cps_nrow != nrow or self.cps_ncol != ncol:
				redraw_table = True				
		except AttributeError:
			redraw_table = True

		if redraw_table:
			# remove old labels
			for widget in frame.winfo_children():
				widget.destroy()

			self.cps_widgets = {}

			for col in range(ncol):
				#colwidth = [max(len(str(r)) for r in df.iloc[:,col])]
				for row in range(nrow):
					if row == 0:
						f = self.headerfont
					else:
						f = self.cellfont
					l = Label(frame, text=str(df.iloc[row, col]), anchor = W, font = f)#, width = colwidth)
					l.grid(row=row, column=col, sticky = W, padx = (10,10))
					self.cps_widgets[(row, col)] = l
					if col == 0:
						l.bind('<Button-1>', self.change_fish)
			self.window.update()

		else:
			for col in range(ncol):
				#colwidth = [max(len(str(r)) for r in df.iloc[:,col])]
				for row in range(nrow):
					if df.iloc[row, col] != self.cps_data.iloc[row, col]:
						self.cps_widgets[(row, col)].configure(text = df.iloc[row, col])
			self.window.update()

		self.cps_data = df
		self.cps_nrow = nrow
		self.cps_ncol = ncol

	def indicate_update(self, col):
		# this function changes the color of the update indicator light
		self.upind.config(bg = col)
	    	self.window.update()

		


def main():
	sbc = App()
	sbc.run()

main()







