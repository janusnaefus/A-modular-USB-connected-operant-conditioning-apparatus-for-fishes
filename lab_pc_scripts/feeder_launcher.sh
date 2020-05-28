#!/bin/bash

# this is the script that should be launched by the user (or automatically launched at startup of a raspberry pi)
# all it does is run a second script (feeder_launcher_stage_2.sh) in a terminal.
# provide your own path to the location where you stored this second script.
lxterminal --command="/home/pi/Desktop/feeder_launcher_stage_2.sh"
