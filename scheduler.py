import time

# Base Scheduler class
#
# Stores
#   - current GPS data
#   - previous GPS data from the last time we sent a packet

class APRSScheduler:
    # Current GPS data to compare against the previous packet data.
    gps_data = None

    # The GPS data from the last time we sent out a packet.
    last_packet_gps_data = None

    # Timestamp of the last packet we sent
    last_packet_timestamp = None

    def ready(self):
        # Overload this function to determine if we're ready to send a packet.
        # True if it's time to send one
        # False if the time is not quite right
        pass


    def sent(self):
        self.last_packet_gps_data = self.gps_data
        self.gps_data = None
        self.last_packet_timestamp = int(time.time())
