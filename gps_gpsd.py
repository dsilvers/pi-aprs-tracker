import dateutil.parser
from gps3 import gps3
import logging
import math

from gps_base import Base_GPS, GPS_Data


class GPSD_Client(Base_GPS):

    def setup(self):
        self.gps_socket = gps3.GPSDSocket()
        self.gps_stream = gps3.DataStream()
        self.gps_socket.connect()
        self.gps_socket.watch()

    def loop(self):
        for tpv_data in self.gps_socket:
            if tpv_data:
                self.gps_stream.unpack(tpv_data)
                tpv = self.gps_stream.TPV

                # Data stream sent by gpsd are sourced from the JSON data as
                # documented here: http://www.catb.org/gpsd/gpsd_json.html
                # Mode is the only field that will ALWAYS be there. Check that
                # we have data for the other fields before expecting them to be there.
                #
                #    mode     GPS fix? 0/1 = none, 2 = 2D, 3 = 3D [we want a 3D fix]

                # Require a 3D fix before continuing
                # Turn off GPS LED if there is no fix
                if tpv['mode'] != 3:
                    logging.info("Waitng for 3D GPS fix")
                    self.gps_data = GPS_Data(fix=False)
                    self.gps_led_pin_off()
                    continue

                previous_fix_status = self.gps_data.fix
                self.gps_data = GPS_Data(fix=True)

                # Turn on the GPS LED if we have a new GPS fix
                if not previous_fix_status:
                    self.gps_led_pin_on()

                logging.info(tpv)

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
                latitude_decimal_degrees = tpv['lat']
                longitude_decimal_degrees = tpv['lon']

                latitude_frac_degrees, latitude_whole_degrees = math.modf(abs(latitude_decimal_degrees))
                longitude_frac_degrees, longitude_whole_degrees = math.modf(abs(longitude_decimal_degrees))

                self.gps_data.latitude = "{:02d}{:05.2f}".format(
                    int(latitude_whole_degrees),
                    latitude_frac_degrees * 60.0,
                )

                self.gps_data.longitude = "{:03d}{:05.2f}".format(
                    int(longitude_whole_degrees),
                    longitude_frac_degrees * 60.0,
                )

                self.gps_data.course = int(round(tpv['track']))
                self.gps_data.speed = int(round(tpv['speed'] / 0.51444))
                self.gps_data.altitude = int(round(tpv['alt'] / 0.3048))

                # Convert ISO 8601 date to a datetime object
                # 2018-03-06T02:43:10.000Z'
                self.gps_data.current_datetime = dateutil.parser.parse(tpv['time'])

                # Initialize the clock as this is the first valid timestamp we
                # have from the GPS data
                if self.start_datetime is None:
                    self.start_datetime = self.gps_data.current_datetime


                if self.scheduler_ready():
                    logging.info("Sending packet")
                    self.send_packet()
                    
