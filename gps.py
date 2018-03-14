import audiogen
import datetime
import logging
from os import system, remove
import RPi.GPIO as GPIO
import time

import afsk.afsk
from afsk.ax25 import UI
from config import *


class GPS_Data:
    def __init__(self, fix=False, latitude=None, longitude=None, altitude=None, 
        course=None, speed=None, current_datetime=None):
        self.fix = fix
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.course = course
        self.speed = speed
        self.current_datetime = current_datetime

    def __str__(self):
        if self.fix:
            fix = "3D FIX"
        else:
            fix = "FIX"
        return "{} {},{}  {} ft  {} deg  {} kts {}".format(
            fix,
            self.latitude,
            self.longitude,
            self.altitude,
            self.course,
            self.speed,
            self.current_datetime,
        )


# GPS base class
# Override the setup and loop methods to create your own GPS readers/parsers
class Base_GPS:
    # Set this to a scheduler class so we can track when messages are sent
    scheduler = None

    # Set this to a GPIO pin to have a LED turn on when we acquire a GPS fix
    # Keep in mind if you don't use of the defined pins in the ALL_OUTPUT_PINS
    # you'll need to manually set it up as a GPIO output. This happens
    # automatically in tracker.py using the pins definied in config.py.
    gps_led_pin = None


    # Setup GPS class
    # For example, our GPSD class creates the gpsd client connection here.
    def setup(self):
        pass


    # Loop here. Receives data from whatever GPS we are using, parses it
    # and determines when to send a packet based on the scheduler class
    # created above.
    #
    # Loop should initialize start_datetime when we have a valid datetime
    # from a GPS or other time source.
    def loop(self):
        pass


    # shutdown method for cleaning up files, closing sockets, etc.
    def shutdown(self):
        pass


    # Initialize the class with empty GPS data and run the setup method
    # to pre-configure our GPS acquiring, assuming our method requires it.
    def __init__(self):
        self.start_datetime = None
        self.gps_data = GPS_Data()

        self.setup()


    # Turn off the GPS LED. Typically this means we lost the GPS fix.
    def gps_led_pin_off(self):
        logging.info("GPS fix lost")
        if self.gps_led_pin:
            GPIO.output(self.gps_led_pin, GPIO.LOW)


    # Turn on the GPS LED, we have acquired a GPS fix.
    def gps_led_pin_on(self):
        logging.info("GPS fix acquired")
        if self.gps_led_pin:
            GPIO.output(self.gps_led_pin, GPIO.HIGH)


    # Check if our scheduler class determines if we are ready to send a packet.
    # Supply it with the current GPS data and the begining time.
    def scheduler_ready(self):
        ready = self.scheduler.ready(
            gps_data=self.gps_data,
            start_datetime=self.start_datetime,
        )

        if ready:
            logging.info("Scheduler says its time to send a packet")
        else:
            logging.info("Scheduler not ready")

        return ready


    # Send out a formatted APRS packet using the current GPS data
    def send_packet(self):
        # Only send a packet if we have a GPS fix
        if not self.gps_data.fix:
            return

        # Format callsign and SSID
        # ABC123-4 with a SSID and ASB123 without one
        if CALLSIGN_SSID == "" or CALLSIGN_SSID == 0:
            callsign = CALLSIGN
        else:
            callsign = "{}-{}".format(CALLSIGN, CALLSIGN_SSID)

        
        # Same thing for the destination and SSID. SSID is not typically used
        # for destinations in the APRS world.
        if DESTINATION_SSID == "" or DESTINATION_SSID == 0:
            destination = DESTINATION
        else:
            destination = "{}-{}".format(DESTINATION, DESTINATION_SSID)


        # Format digipeater paths. These are split by commas and properly encoded
        # in a bytestream, as they are a key ingredient in generating the CRC bits.
        digipeaters = DIGIPEATING_PATH.split(b',')


        # Determine proper N/S/E/W directions
        if self.gps_data.latitude < 0.0:
            latitude_direction = "S"
        else:
            latitude_direction = "N"

        if self.gps_data.longitude < 0.0:
            longitude_direction = "W"
        else:
            longitude_direction = "E"


        # Format APRS info string
        # APRS Info string goes something like this:
        # /235619h4304.95N/08912.63W>000/003/A=000859 comment

        info = "/{:%H%M%S}h{}{}{}{}{}{}{:03d}/{:03d}/A{:06d} {}".format(
            self.gps_data.current_datetime,         # datetime object
            self.gps_data.latitude,                 # 04304.95
            latitude_direction,                     # N/S
            APRS_SYMBOL1,                           # Symbol lookup table, see config
            self.gps_data.longitude,                # 08912.63
            longitude_direction,                    # E/W
            APRS_SYMBOL2,                           # Symbol lookup table, see config
            self.gps_data.course,                   # Magnetic heading
            self.gps_data.speed,                    # Speed in knots
            self.gps_data.altitude,                 # Altitude to meters
            APRS_COMMENT,                           # Set comment text in config
        )

        logging.info("{}>{},{}:{}".format(
            callsign,
            destination,
            DIGIPEATING_PATH,
            info,
        ))


        # Create packet. This formats the headers with CRC checksums and all that
        # stuff that we're grateful we didn't have to figure out ourselves.
        packet = UI(
                source=callsign,
                destination=destination,
                digipeaters=digipeaters,
                info=info,
        )
        audio = afsk.encode(packet.unparse())


        # Sometimes for debugging saving the generated .wav is helpful.
        # Make sure this location is in a ramdisk!
        with open("/tmp/output.wav", "w") as f:
            audiogen.sampler.write_wav(f, audio)
            

        # Enable radio transmit push-to-talk pin by driving it high.
        GPIO.output(RADIO_TX_PIN, GPIO.HIGH)

        # Wait for the PTT to activate and the radio to actually be transmitting.
        # Also gives iGates and clients a chance to listen for the actual message.
        # However... we don't want to set this too long or we just consume valuable
        # airtime.
        time.sleep(RADIO_TX_DELAY / 1000.0)

        # Play the audio sample out the PWM pin
        # For some reason this results in garbled audio
        #audiogen.sampler.play(audio, blocking=True)

        system("play -q /tmp/output.wav")
        #remove("/tmp/output.wav")

        # Disable radio transmit
        GPIO.output(RADIO_TX_PIN, GPIO.LOW)


        # Signal to the scheduler that we sent a packet
        self.scheduler.sent(self.gps_data)

