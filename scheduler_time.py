from scheduler import APRSScheduler
from config import SCHEDULER_TIME_INTERVAL

import time


class TimerScheduler(APRSScheduler):
    """
    Very simple scheduler. Send a message every SCHEDULER_TIME_INTERVAL seconds.
    Returns True if we're ready to send our message.
    """

    def ready(self):

        if int(time.time()) - self.last_packet_timestamp > SCHEDULER_TIME_INTERVAL:
            return True

        return False