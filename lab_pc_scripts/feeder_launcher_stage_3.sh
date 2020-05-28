#!/bin/bash

# one argument needs to be passed to this function, namely the pi_id of this machine
# this is used to name the debug file.
# provide your own path to this debug file. all output from the controlling program will be logged to this file, which should be on the network drive so you can check it remotely.
debuglog="/home/pi/HasliJannaef/skinner_box_settings/currently_running/${1}_debug.txt"

echo |& tee -a $debuglog
echo |& tee -a $debuglog
echo |& tee -a $debuglog
echo "new session..." |& tee -a $debuglog
date |& tee -a $debuglog
echo |& tee -a $debuglog
echo |& tee -a $debuglog

# this is where the controlling program (main_control.py) is started. provide the path to the network drive where you stored this program.
python /home/pi/HasliJannaef/skinner_box_settings/currently_running/main_control.py |& tee -a $debuglog
