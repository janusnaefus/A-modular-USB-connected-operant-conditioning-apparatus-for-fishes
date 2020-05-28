
import datetime

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


# a dictionnary to assign colors to tasks in the plot
tcol = {}

alpha = 0.5

tcol['task recording'] = (0.0, 0.0, 0.0, alpha)

tcol['task feed_only_a_190719'] = (0.0, 1.0, 0.0, alpha)
tcol['task feed_only_b_190719'] = (0.0, 1.0, 0.0, alpha)

tcol['task social_learning_symetrical_1_a_190628'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_symetrical_2_a_190628'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_symetrical_3_a_190628'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_symetrical_1_b_190628'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_symetrical_2_b_190628'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_symetrical_3_b_190628'] = (0.0, 0.0, 0.0, alpha)


tcol['task cooperation_training_rf_a_15s_190715'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_rf_b_15s_190715'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_gf_a_15s_190715'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_training_gf_b_15s_190715'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_training_bf_a_15s_190715'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_training_bf_b_15s_190715'] = (0.0, 0.0, 1.0, alpha)

tcol['task cooperation_training_rf_a_short_190628'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_rf_b_short_190628'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_gf_a_short_190628'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_training_gf_b_short_190628'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_training_bf_a_short_190628'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_training_bf_b_short_190628'] = (0.0, 0.0, 1.0, alpha)

tcol['task social_learning_teacher_a_long_190618'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_teacher_b_long_190618'] = (0.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_rf_a_190618'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_rf_b_190618'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_training_gf_a_190618'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_training_gf_b_190618'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_training_bf_a_190618'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_training_bf_b_190618'] = (0.0, 0.0, 1.0, alpha)

tcol['task cooperation_possible_rf_a_190612'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_possible_rf_b_190612'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_possible_rn_a_190612'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_possible_rn_b_190612'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_possible_rc_a_190612'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_possible_rc_b_190612'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_possible_gf_a_190612'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_possible_gf_b_190612'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_possible_gn_a_190612'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_possible_gn_b_190612'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_possible_gc_a_190612'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_possible_gc_b_190612'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_possible_bf_a_190612'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_possible_bf_b_190612'] = (0.0, 1.0, 0.0, alpha)
tcol['task cooperation_possible_bn_a_190612'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_possible_bn_b_190612'] = (1.0, 0.0, 0.0, alpha)
tcol['task cooperation_possible_bc_a_190612'] = (0.0, 0.0, 1.0, alpha)
tcol['task cooperation_possible_bc_b_190612'] = (0.0, 0.0, 1.0, alpha)
tcol['task social_learning_teacher_a_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_teacher_b_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_a_1_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_a_2_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_a_3_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_a_4_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_a_5_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_b_1_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_b_2_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_b_3_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_b_4_190612'] = (0.0, 0.0, 0.0, alpha)
tcol['task social_learning_student_b_5_190612'] = (0.0, 0.0, 0.0, alpha)


tcol['task shelter_training_190328']                      = (0.1, 0.5, 0.0, alpha)
tcol['task shelter_training_phase_2_190401']              = (0.2, 0.4, 0.0, alpha)
tcol['task shelter_training_phase_3_190402']              = (0.3, 0.3, 0.0, alpha)
tcol['task shelter_training_phase_4_190403']              = (0.4, 0.2, 0.0, alpha)
tcol['task shelter_training_phase_5_190405']              = (0.5, 0.1, 0.0, alpha)

tcol['task outside_training_phase_0_190417']              = (0.1, 0.5, 0.0, alpha)
tcol['task outside_training_phase_1_190408']              = (0.3, 0.5, 0.0, alpha)

tcol['task vibration_detection_short_feed_190417']        = (0.1, 0.0, 0.5, alpha)
tcol['task vibration_detection_long_nothing_190417']      = (0.3, 0.0, 0.5, alpha)

tcol['task vibration_detection_short_feed_190417_test']   = (0.1, 0.0, 0.0, alpha)
tcol['task vibration_detection_long_nothing_190417_test'] = (0.1, 0.0, 0.0, alpha)

tcol['task color_detection_red_feed_190503']              = (0.1, 0.9, 0.0, alpha)
tcol['task color_detection_green_nothing_190503']         = (0.9, 0.1, 0.0, alpha)
tcol['task color_detection_short_red_feed_190508']        = (0.1, 0.9, 0.0, alpha)
tcol['task color_detection_short_green_nothing_190508']   = (0.9, 0.1, 0.0, alpha)

tcol['task rgb_red_training_190605']                      = (1.0, 0.0, 0.0, alpha)
tcol['task rgb_green_training_190605']                    = (0.0, 1.0, 0.0, alpha)
tcol['task rgb_blue_training_190605']                     = (0.0, 0.0, 1.0, alpha)

tcol['task red_training_190513']                          = (1.0, 0.1, 0.0, alpha)
tcol['task red_green_training_190516']                    = (1.0, 0.2, 0.0, alpha)
tcol['task test_1']                                       = (1.0, 0.3, 0.0, alpha)
tcol['task feed_only_190418']                             = (1.0, 0.4, 0.0, alpha)
tcol['task test_devices_190502']                          = (1.0, 0.5, 0.0, alpha)

class skinnerplot:
	def __init__(self):
		self.fig = Figure(figsize=(5, 4), dpi=100)
		self.ax = self.fig.add_subplot(111)

		days = mdates.DayLocator(interval = 10)
		days_fmt = mdates.DateFormatter('%m-%d')
		self.ax.xaxis.set_major_formatter(days_fmt)
		self.ax.xaxis.set_major_locator(days)

	def draw(self, d):

		# remove the old data points
		while(len(self.ax.lines) > 0):
			self.ax.lines[0].remove()

		for s in d.task.unique():
			temp = d[d.task == s]
			self.ax.plot(temp.time, temp.trigger_delay, 'o', color = tcol[s], label = s, markersize = 4)

		#self.ax.legend()

		self.ax.set_xlim(d.time.min() - datetime.timedelta(days=1), d.time.max() + datetime.timedelta(days=1))
		self.ax.set_ylim(d.trigger_delay.min() - 10, d.trigger_delay.max() + 10)

		self.fig.autofmt_xdate()

		return self.fig












