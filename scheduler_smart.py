import scheduler_base 
from config import BEACON_FAST_SPEED, BEACON_FAST_RATE, BEACON_SLOW_SPEED, \
    BEACON_SLOW_RATE, BEACON_MIN_TURN_TIME, BEACON_MIN_TURN_ANGLE, \
    BEACON_TURN_SLOPE

import logging


class SmartScheduler(scheduler_base.APRSScheduler):
    """
        SmartBeaconing scheduler based on a modified version of the 
        SmartBeaconing and CornerPegging algorithm.
        Further algorithm details can be found here:
        http://www.hamhud.net/hh2/smartbeacon.html
        http://info.aprs.net/index.php?title=SmartBeaconing
    """

    def ready(self, gps_data, start_datetime):

        # First packet of the loop, always just send it.
        if not self.last_packet_gps_data:
            return True

        # Calculate the total number of seconds since the last packet.
        seconds_since_last = (gps_data.current_datetime - self.last_packet_gps_data.current_datetime).total_seconds()

        # First determine beacon speed based on GPS speed.
        # If we're moving slower, transmit less often.
        # If we're moving faster, transmit more often.
        # This is all configurable in the config, so you could easily change
        # this behavior yourself however you see fit.
        if gps_data.speed < BEACON_SLOW_SPEED:
            # Slow speed. Transmit less often.
            logging.info("BEACONING: Slow speed {} < {}".format(gps_data.speed, BEACON_SLOW_SPEED))
            beacon_rate = BEACON_SLOW_RATE
        else:
            if gps_data.speed > BEACON_FAST_SPEED:
                # Fast speed.
                logging.info("BEACONING: Fast speed {} < {}".format(gps_data.speed, BEACON_FAST_SPEED))
                beacon_rate = BEACON_FAST_RATE
            else:
                # Medium speed.
                logging.info("BEACONING: Medium speed {} --".format(gps_data.speed))
                beacon_rate = BEACON_FAST_RATE * BEACON_FAST_SPEED / gps_data.speed


            # CornerPegging logic
            # Detects if we've made a rapid change in course that would suggest
            # we should be transmitting again.
            # Calculate the amount the course has changed since the last packet.
            course_change = abs(self.last_packet_gps_data.course - gps_data.course)
            course_change_angle_rate = BEACON_MIN_TURN_ANGLE + BEACON_TURN_SLOPE / gps_data.speed
            logging.info("BEACONING: CornerPegging check - course change {} > angle rate {}, seconds since last {} > min turn time {}".format(course_change, course_change_angle_rate, seconds_since_last, BEACON_MIN_TURN_TIME))
            # If the course has made signifigant change and the minimum amount of time
            # between packets has been exceeded, it's time to send a packet.
            if  course_change > course_change_angle_rate and \
                seconds_since_last > BEACON_MIN_TURN_TIME:

                seconds_since_last = beacon_rate;
                logging.info("BEACONING: CornerPegging is active, we are turning!")


        # IF the amount of time that has passed since the last packet is higher
        # than the beacon rate, send the packet.
        logging.info("BEACONING: Beacon rate is {}, seconds since last is {}".format(beacon_rate, seconds_since_last))            
        if seconds_since_last >= beacon_rate:
            logging.info("BEACONING: Time to send packet. seconds since last {} > beacon rate {}".format(seconds_since_last, beacon_rate))
            return True

        return False
