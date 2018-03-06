import audiogen
import dateutil.parser
import logging
import math
from os import system, remove
import RPi.GPIO as GPIO
import time

import afsk.afsk
from afsk.ax25 import UI
from config import *


def send_packet(gps_data):

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


    # Data stream sent by gpsd are sourced from the JSON data as
    # documented here: http://www.catb.org/gpsd/gpsd_json.html
    # Mode is the only field that will ALWAYS be there. Check that
    # we have data for the other fields before expecting them to be there.
    #
    # Fields that interest us:
    #    mode     GPS fix? 0/1 = none, 2 = 2D, 3 = 3D [we want a 3D fix]
    #    lon      Longitude
    #    lat      Latitude
    #    alt      Altitude
    #    time     Time/date stamp in ISO8601 format, UTC
    #    track    Course in degrees from true north
    #    speed    Speed in meters per second
    #    climb    Climb rate (or sink) in meters per second

    # Parse Longitude and latitude, convert from decimal degrees to degrees and
    # decimal minutes.
    latitude_decimal_degrees = gps_data['lat']
    longitude_decimal_degrees = gps_data['lon']

    latitude_frac_degrees, latitude_whole_degrees = math.modf(abs(latitude_decimal_degrees))
    longitude_frac_degrees, longitude_whole_degrees = math.modf(abs(longitude_decimal_degrees))

    latitude = "{:02d}{:05.2f}".format(
        int(latitude_whole_degrees),
        latitude_frac_degrees * 60.0,
    )

    longitude = "{:03d}{:05.2f}".format(
        int(longitude_whole_degrees),
        longitude_frac_degrees * 60.0,
    )

    # Determine proper N/S/E/W directions
    if gps_data['lat'] < 0.0:
        latitude_direction = "S"
    else:
        latitude_direction = "N"

    if gps_data['lon'] < 0.0:
        longitude_direction = "W"
    else:
        longitude_direction = "E"

    # Convert ISO 8601 date to a datetime object
    # 2018-03-06T02:43:10.000Z'
    gps_time = dateutil.parser.parse(gps_data['time'])


    # Format APRS info string
    # APRS Info string goes something like this:
    # /235619h4304.95N/08912.63W>000/003/A=000859 comment

    info = "/{:%H%M%S}h{}{}{}{}{}{}{:03d}/{:03d}/A{:06d} {}".format(
        gps_time,                               # datetime object
        latitude,                               # 04304.95
        latitude_direction,                     # N/S
        APRS_SYMBOL1,                           # Symbol lookup table, see config
        longitude,                              # 08912.63
        longitude_direction,                    # E/W
        APRS_SYMBOL2,                           # Symbol lookup table, see config
        int(round(gps_data['track'])),                      # Magnetic heading
        int(round(gps_data['speed'] / 0.51444)),# Speed in knots
        int(round(gps_data['alt'] / 0.3048)),   # Convert altitude to meters
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


