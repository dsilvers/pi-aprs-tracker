from gps3 import gps3
from datetime import datetime, date, time, timedelta
import dateutil.parser

gps_socket = gps3.GPSDSocket()
data_stream = gps3.DataStream()
gps_socket.connect()
gps_socket.watch()

day_start = date.today()
fix_time = None
current_time = None

midnight = datetime.combine(
    day_start,
    time(0, 0, 0),
)

for new_data in gps_socket:
    if new_data:
        data_stream.unpack(new_data)

        print data_stream.TPV

        if data_stream.TPV['mode'] != 3:
            continue

        lat = data_stream.TPV['lat']
        lon = data_stream.TPV['lon']
        alt = data_stream.TPV['alt']
        gps_time = data_stream.TPV['time']

        if lat < 0.0:
            lat_d = "S"
        else:
            lat_d = "N"

        if lon < 0.0:
            lon_d = "W"
        else:
            lon_d = "E"

        # 2018-03-06T02:43:10.000Z'
        dt = dateutil.parser.parse(gps_time)

        if fix_time is None:
            fix_time = dt

        current_time = dt

        # test creating a date object with just knowing the seconds since midnight, 
        # GDL90 data will only give us the seconds since midnight
        manufactured_dt  = datetime.combine(
            day_start,
            time(dt.hour, dt.minute, dt.second),
        )

        seconds_since_midnight = int((manufactured_dt - midnight).total_seconds())

        """
        # after more testing, this octal stuff isn't really testing well or
        # probably necessary, but i'll keep it here just in case
        #
        # date math really is a pain.
        octal_seconds_since_midnight = int(seconds_since_midnight, 8)
        print type(octal_seconds_since_midnight)
        octal_dt = datetime.combine(
            day_start,
            time(0, 0, 0),
        ) + timedelta(seconds=int(octal_seconds_since_midnight))
        """

        magical_math_date = datetime.combine(
            day_start,
            time(0, 0, 0),
        ) + timedelta(seconds=int(seconds_since_midnight))

        print "Lat: {:05.2f}{}".format(abs(lat) * 100.0, lat_d)
        print "Lon: {:05.2f}{}".format(abs(lon) * 100.0, lon_d)
        print "Alt: {:06d} meters or {:06d} feet".format(int(round(alt)), int(round(alt / 0.3048)))
        print "GPS Timestamp: {} ".format(gps_time)
        print "Time: {:%H%M%S}h".format(dt)
        print "Running since for seconds: {}".format((current_time - fix_time).total_seconds())
        print "Day Start: {}".format(day_start)
        print "Seconds since midnight: {}".format(seconds_since_midnight)
        print "Calculated date, should match the other one: {:%H%M%S}h".format(magical_math_date)


