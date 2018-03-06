# Some of the comments blurbs here are sourced from the Trackuino project.


# Set your callsign and SSID here. 
#
# Common values for the SSID are
#   (from http://zlhams.wikidot.com/aprs-ssidguide):
# - Balloons:  11
# - Aircraft:  11
# - Cars:       9
# - Boats:      8
# - Home:       0
# - IGate:      5
CALLSIGN = "KD9KEO"
CALLSIGN_SSID = 9


# Destination callsign. APRS uses this to identify your hardware type. We
# set an experimental type, because that seems to make sense. You can also
# just use 'APRS', but direwolf and some clients during debugging gave me
# warnings, so I set something else.
# Defining a destination with APRS and SSID=0 is "usually OK".
#
# Full list of "TO" calls is here:
# http://www.aprs.org/aprs11/tocalls.txt
DESTINATION      "APZ999"
DESTINATION_SSID = 0


# Digipeating paths:
# (read more about digipeating paths here: http://wa8lmf.net/DigiPaths/ )
#
# The recommended digi path for a balloon is "WIDE2-1" or pathless.
#
# A vehicle or another low ground-based tracker may require help getting to
# a relay, therefore "WIDE1-1,WIDE2-2" might work better. In some places even
# an airborne target (flying in the mountains?) may require more hops to get
# to a gateway.
DIGIPEATING_PATH = "WIDE1-1,WIDE2-2"


# APRS symbol for aprs.fi and others
# https://github.com/wb2osz/direwolf/blob/612c2dc92887f393c84215d07bf374e045e569b6/symbols-new.txt
# example: 1->'/' and 2->'>' is a car
# example: 1->'/' and 2->'\'' is a small aircraft
APRS_SYMBOL1 = '/'
APRS_SYMBOL2 = '>'



# APRS comment: this goes in the comment portion of the APRS message. You
# might want to keep this short. The longer the packet, the more vulnerable
# it is to noise.
APRS_COMMENT = "aprs-pi"


# Specify the scheduler class you would like to use
#
# - "time" sends a packet at a fixed time (once every SCHEDULER_TIME_INTERVAL seconds)
#         > see scheduler_time.py
#
# - "smart" is the SmartBeaconing and CornerPegging algorithim
#         > see scheduler_smart.py
#
# - "custom?", specify your own? write your own?
#
SCHEDULER = "time"

# If using the time scheduler, send a packet every 60 seconds
SCHEDULER_TIME_INTERVAL = 60


# SmartBeaconing and CornerPegging configuration
# Further algorithm details can be found here:
#    http://www.hamhud.net/hh2/smartbeacon.html
#    http://info.aprs.net/index.php?title=SmartBeaconing
BEACON_FAST_SPEED =     60
BEACON_FAST_RATE  =     180
BEACON_SLOW_SPEED =     4
BEACON_SLOW_RATE  =     600
BEACON_MIN_TURN_TIME =  15
BEACON_MIN_TURN_ANGLE = 30
BEACON_TURN_SLOPE =     255


# GPIO pins for turning on LED's and enabling the radio to transmit. 
# The Radiometrix pin #4 set high signals the module to transmit.
# Yellow LED is used for the GPS lock.
# Green LED is used to signal that the script is running.
RADIO_TX_PIN = 23
YELLOW_LED_PIN = 24
GREEN_LED_PIN = 25


# Radiometrix PWM pin for transmiting the AX.25 packets. We actually will
# set the Pi to redirect audio to this pin. Use `raspi-gpio set PIN# a5`.
#
# More details in this excellent Stack Overflow post:
# https://raspberrypi.stackexchange.com/questions/49600/how-to-output-audio-signals-through-gpio
RADIO_PWM_PIN = 18


# Easy to access list of all pins for our setup purposes
ALL_OUTPUT_PINS = [RADIO_TX_PIN, YELLOW_LED_PIN, GREEN_LED_PIN, RADIO_PWM_PIN]


# How long to wait after turning on the transmitter to begin playing the AX.25
# transmission? Trackuino uses 300 milliseconds.
RADIO_TX_DELAY = 300

