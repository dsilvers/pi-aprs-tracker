from gps3 import gps3
from datetime import datetime
import dateutil.parser

gps_socket = gps3.GPSDSocket()
data_stream = gps3.DataStream()
gps_socket.connect()
gps_socket.watch()
for new_data in gps_socket:
    if new_data:
        data_stream.unpack(new_data)

        print data_stream.TPV

        if data_stream.TPV['mode'] != 3:
            continue

        lat = data_stream.TPV['lat']
        lon = data_stream.TPV['lon']
        alt = data_stream.TPV['alt']
        time = data_stream.TPV['time']

        if lat < 0.0:
            lat_d = "S"
        else:
            lat_d = "N"

        if lon < 0.0:
            lon_d = "W"
        else:
            lon_d = "E"

        # 2018-03-06T02:43:10.000Z'
        dt = dateutil.parser.parse(time)

        print "Lat: {:05.2f}{}".format(abs(lat) * 100.0, lat_d)
        print "Lon: {:05.2f}{}".format(abs(lon) * 100.0, lon_d)
        print "Alt: {:06d} meters or {:06d} feet".format(int(round(alt)), int(round(alt / 0.3048)))
        print "GPS Timestamp: {} ".format(time)
        print "Time: {:%H%M%S}h".format(dt