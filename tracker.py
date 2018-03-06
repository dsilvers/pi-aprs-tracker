#!/usr/bin/env python

from gps3 import gps3
import logging
from os import system
import RPi.GPIO as GPIO
import sys
import time

from aprs import send_packet
from config import *


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if SCHEDULER == "time":
    from scheduler.scheduler_time import TimerScheduler as Scheduler


# TODO
# test GPS disconnecting
# test GPSD dying
# fstab -> tmpdisk
# tune amount of tx delay (doesn't seem to make a difference)


def main():
    # Configure our LED and TX pins
    #GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ALL_OUTPUT_PINS, GPIO.OUT, initial=GPIO.LOW)

    # Python GPIO library does not support setting the special modes
    # of the pins, so we have to call an external command for that.
    # This enables us to pipe the audio out of the PWM pin directly to the
    # radio.
    system("raspi-gpio set {} a5".format(RADIO_PWM_PIN))

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
            tpv = gps_stream.TPV

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
            if not scheduler.last_packet_gps_data or \
                scheduler.last_packet_gps_data['mode'] != 3:
                GPIO.output(YELLOW_LED_PIN, GPIO.HIGH)

            scheduler.gps_data = tpv
            if scheduler.ready():
                logger.info(tpv)
                logger.info("Sending packet")
                send_packet(tpv)
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
