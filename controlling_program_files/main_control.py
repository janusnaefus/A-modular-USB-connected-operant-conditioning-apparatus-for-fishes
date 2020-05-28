
import sys


import device_control
import skinnerbox_errors as errors
import skinnerbox_interThreadCommunication as interThreadCom

def main():
	itc = interThreadCom.interThreadCom()
	try:
		p = device_control.devices()
		p.run()
	except errors.FatalError as e:
		print "Fatal Error: " + str(e)
		return 0
	except KeyboardInterrupt:
		print "keyboard interrupt in main"
	finally:
		itc.stop_all_tanks_flag.set()
		
	return 0

main()
