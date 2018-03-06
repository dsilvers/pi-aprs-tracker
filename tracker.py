from gps3 import gps3
import logging
import RPi.GPIO as GPIO
import sys
import time

from config import *
from schedule_time import TimerScheduler


logger = logging.getLogger(__name__)

if SCHEDULER == "time":
    from schedule_time import TimerScheduler as Scheduler



# TODO
# test GPS disconnecting
# test GPSD dying


def main():
    # Configure our LED and TX pins
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ALL_OUTPUT_PINS, GPIO.OUT, initial=GPIO.LOW)

    # Script running, turn on the green LED
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH)


    # Setup our connection to the gpsd daemon.
    # We will iterate through the data sent through the socket connection.
    gps_socket = gps3.GPSDSocket()
    gps_stream = gps3.DataStream()
    gps_socket.connect()
    gps_socket.watch()

    scheduler = Scheduler()

    for gps_data in gps_socket:
        if gps_data:
            gps_stream.unpack(gps_data)
            tpv = data_stream.TPV

            # Data stream sent by gpsd are sourced from the JSON data as
            # documented here: http://www.catb.org/gpsd/gpsd_json.html
            # Mode is the only field that will ALWAYS be there. Check that
            # we have data for the other fields before expecting them to be there.
            #
            #    mode     GPS fix? 0/1 = none, 2 = 2D, 3 = 3D [we want a 3D fix]

            # Require a 3D fix before continuing
            # Turn off GPS LED if there is no fix
            if tpv['mode'] != 3:
                logger.info("Waitng for 3D GPS fix")
                GPIO.output(YELLOW_LED_PIN, GPIO.LOW)
                continue

            # Turn on the GPS LED if we have a new GPS fix
            if scheduler.last_packet_gps_data and \
                scheduler.last_packet_gps_data['mode'] != 3:
                GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)

            scheduler.gps_data = tpv
            if scheduler.ready():
                logger.info("Sending packet")
                aprs_send_packet(tpv)
                scheduler.sent()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        # Turn off the lights
        GPIO.output(ALL_OUTPUT_PINS, GPIO.LOW)
        GPIO.cleanup()
        
        # Close the door
        sys.exit(0)
