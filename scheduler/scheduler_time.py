from .scheduler import APRSScheduler
from config import SCHEDULER_TIME_INTERVAL

import time


class TimerScheduler(APRSScheduler):
    """
    Very simple scheduler. Send a message every SCHEDULER_TIME_INTERVAL seconds.
    Returns True if we're ready to send our message.
    """

    def ready(self, gps_data, start_datetime):

        # Probably should log this one, could get stuck here I guess
        if start_datetime is None:
            return False

        # First packet of the loop, always just send it
        if not self.last_packet_gps_data:
            return True


        if (gps_data.current_datetime - self.last_packet_gps_data.current_datetime).total_seconds() >= SCHEDULER_TIME_INTERVAL:
            return True

        return False