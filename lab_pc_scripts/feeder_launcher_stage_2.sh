#!/bin/bash

# this script first waits for the network connection to settle
# then mounts a network drive
# then starts another script which will run the python program and log its output to a debug file
# it then checks every PERIOD seconds whether one of the flag files in a given list has been modified (these flag files are used as 'commands' to indicate that the program should be reloaded, see below).
# if this is the case, it kills all python processes and restarts the given python script.


# because you may be working with several controlling pcs, each of these devices needs to know its own identity.
# on a raspberry pi, this is done by reading a file where the information about the cpu serial number can be found
# see also the functions read_serial and determine_pi_id below
# for other types of devices, you may have to specify your own identification method
# alternatively, if the device you are working with does not contain this file, or the file does not contain a serial number, you can create the file and/or modify it to contain a unique serial number that identifies each device.
serial_file='/proc/cpuinfo'

# file to which starting and restarting information is written locally.
# this is different from the file to which the output of the python script is redirected (see feeder_launcher_stage_2.sh)
# provide your own path.
LOGFILE='/home/pi/Desktop/restart_log.txt'

# wait PERIOD seconds between checking the flag files
PERIOD=1
# a variable to store whether the flag files are currently up to date
UP_TO_DATE=true

# this function writes information passed to it to a logfile (see above), preceded by the date
function writelog {
  now=`date`
  echo "$now $*" >> $LOGFILE
  echo "$now $*"
}

# this function waits for an internet connection, sets the clock, and then returns
function setclock {
	# turn off the automatic time-setting service of systemd (usually turning this service off and on again will sync the time, but this has failed in the past. therefore the time is synced manually in-between)
	echo
	echo "turning timedatectl service off"
	sudo timedatectl set-ntp false
	echo "ok"
	
	# get the time from a header of the google page and convert it to the format required by timedatectl
	echo
	echo "getting time from google page header"
	time=""
	while true ; do
		time="$(wget -qSO- --max-redirect=0 google.com 2>&1 | grep Date: | cut -d' ' -f5-8)"
		if [ -n "$time" ] ; then
			break
		fi
		echo "..."
		sleep 1
	done
	# the Z is needed to account for the daylight saving time i think. the date command converts between time formats
	time="${time}Z"
	time="$(date --date "$time" +%Y-%m-%d\ %H:%M:%S)"
	echo $time
	echo "ok"
	
	# convert this time to a format which timedatectl can read, and set the time
	echo
	echo "setting system time"
	sudo timedatectl set-time "$time"
	echo "ok"
	
	# turn automatic syncing back on
	echo
	echo "turning timedatectl service back on"
	sudo timedatectl set-ntp true
	echo "ok"
	
	# tell the user what time it is now
	echo "the time is now set to $(date)"
}

# connect to the network drive using cifs
# provide your own network drive path, login credentials and user id. refer to the documentation of cifs if you are having trouble with this, and talk to the person who set up the network drive.
function mount_network_drives {
	sudo mount -t cifs [network drive location] [mounting point] -o username=[username],domain=[domain],password=[password],uid=[user ID];
}

# find the serial number of a raspberry pi zero w in the file given above
function read_serial {
	local serial="0"
	while IFS='\n' read -r line ; do
		if [[ "${line:0:6}" == "Serial" ]] ; then
			serial=${line:10:16}
		fi
	done < $1
	echo $serial
}

# match the serial number to a name given to this device
# this is also done in the file 'device_control.py', and the mapping given here should correspond to the mapping in this file
# see the dictionnary serial_numbers and the function devices::parse_id in device_control.py
function determine_pi_id {
	local hw_id="0"
	if [[ "$1" == "00000000d0959c08" ]] ; then
		hw_id="PI_001"
	fi
	if [[ "$1" == "00000000ddb07dca" ]] ; then
		hw_id="PI_002"
	fi
	if [[ "$1" == "0000000023a916b3" ]] ; then
		hw_id="PI_003"
	fi
	if [[ "$1" == "0000000055128134" ]] ; then
		hw_id="PI_004"
	fi
	if [[ "$1" == "00000000d8ca3ccd" ]] ; then
		hw_id="PI_005"
	fi
	if [[ "$1" == "000000002bf030d6" ]] ; then
		hw_id="PI_006"
	fi
	if [[ "$1" == "0" ]] ; then
		hw_id="Laptop"
	fi
	echo $hw_id
}

echo
echo "determining which hardware this script is running on"
serial=$(read_serial $serial_file)
echo "serial: $serial"
pi_id=$(determine_pi_id $serial)
echo "hardware ID: $pi_id"
echo "ok"


# try setting the clock. this function returns when it is able to retreive the clock from google and thus guarantees that the internet connection is working and the time is up-to-date
echo
echo "waiting for network and clock setting..."
echo
setclock
echo
echo "ok"


# connect the network drives.
echo
echo "connecting network drives..."
mount_network_drives
echo "ok"
echo


# this array contains the reload flag for this lab pc and one common reload flag for all lab pcs.
# lab pcs can be told to reload the program code by "touching" one of these files, i.e. changing the modification date.
# provide your own path (to the network drive mounted above) and file names. the file names should correspond to the file names specified in the monitor program (which can be used to command the lab pcs to reload)
# note that the name of the first file (the reload flag for this specific lab pc) contains the id of this device, as determined above.
declare -a FILES
FILES[0]="/home/pi/HasliJannaef/skinner_box_settings/currently_running/reload_python_code_flag_${pi_id}.txt"
FILES[1]="/home/pi/HasliJannaef/skinner_box_settings/currently_running/reload_python_code_flag_all.txt"

# store the modification times in an array. newtimes will be updated periodically and compared to oldtimes
echo "getting modification times of requested files..."
declare -a OLDTIMES
declare -a NEWTIMES
# just an index for the loop
INDEX=0
for f in "${FILES[@]}" ; do
	echo "$f"
	OLDTIMES[$INDEX]=$(stat "$f" -c %Y)
	# output this in human-readable format
	date --date "@${OLDTIMES[$INDEX]}"
	NEWTIMES[$INDEX]=${OLDTIMES[$INDEX]}
	INDEX=$(expr $INDEX + 1)
done
echo "done"
echo



writelog "Starting"

# this loop runs forever, restarting the command if one of the files has been changed
while true ; do
	# run the command in a new window
	# provide the path to where you put the file feeder_launcher_stage_2.sh
	lxterminal --command="/home/pi/Desktop/feeder_launcher_stage_3.sh $pi_id"
	
	# start a loop that checks the modification times every now and then
	while true ; do
		# just an index for the loop
		INDEX=0
		for f in "${FILES[@]}" ; do
			# update new modification time and compare it to the old one
			NEWTIMES[$INDEX]=$(stat $f -c %Y)
			if [[ ${OLDTIMES[$INDEX]} != ${NEWTIMES[$INDEX]} ]] ; then
				# if it has been changed, write this to the log and exit the loop (see below)
				writelog "$f has changed"
				UP_TO_DATE=false
			fi
			INDEX=$(expr $INDEX + 1)
		done
		if [[ $UP_TO_DATE == false ]] ; then
			break
		fi
		sleep $PERIOD
	done
	INDEX=0
	# you get here only if one of the files has been modified. if so, update the new modification times.
	for f in "${FILES[@]}" ; do
		OLDTIMES[$INDEX]=${NEWTIMES[$INDEX]}
		INDEX=$(expr $INDEX + 1)
	done
	# then say that all files are up to date again, kill all running python processes and continue with the endless loop.
	UP_TO_DATE=true
	pkill -9 python
	writelog "Restarting..."
done




echo
echo
echo "press enter to continue"
read
