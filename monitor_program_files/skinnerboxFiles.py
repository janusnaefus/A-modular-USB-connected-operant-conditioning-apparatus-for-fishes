
import os


working_directory  = os.path.dirname(os.path.realpath(__file__)) + '/'
#remote_data_folder = "/home/jan/HasliJannaef/skinner_box_settings/test_setup/"
remote_data_folder = "/home/jan/HasliJannaef/skinner_box_settings/currently_running/"
#remote_data_folder = working_directory  + "NewData/"
local_data_folder  = working_directory  + "RawData/"
data_filename      = working_directory  + "data.csv"
metadata_filename  = working_directory  + "metadata.csv"
#config_filename    = working_directory  + "training_protocol.txt"
config_filename    = remote_data_folder + "training_protocol.txt"
