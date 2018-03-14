#
# decoder.py
#

from collections import deque
import datetime
import messages
import logging
from gdl90.fcs import crcCheck
import sys


class Decoder(object):
    """GDL-90 data link interface decoder class"""

    def __init__(self):
        self.inputBuffer = bytearray()
        self.messages = deque()
        self.parserSynchronized = False

        # lat, lon, course, speed reporting
        self.latitude = 0.0
        self.longitude = 0.0
        self.course = None
        self.speed = None
        self.pressure_altitude = None
        self.altitude = None
        self.vertical_speed = 0.0   # fpm
        self.nic = 0        # >= 8 is probably great for us
        self.nac = 0         # >= 8 is probably great for us

        self.gpsAge = 9999
        self.gpsMaxAge = 5
        
        self.seconds_since_midnight = 0
        self.current_datetime = datetime.datetime.combine(
            datetime.date.today(),
            datetime.time(0, 0, 0),
        )


    @property
    def fix(self):
        # Check if we have a recent GPS fix
        if self.nac >= 8 and self.gpsAge < self.gpsMaxAge:
            return True
        return False
    
    
    def addBytes(self, data):
        """add raw input bytes for decode processing
        returns None or whatever the message number that was processed"""
        self.inputBuffer.extend(data)
        return self._parseMessages()
    
    
    def _log(self, msg):
        sys.stderr.write('decoder.Decoder:' + msg + '\n')
    
    def _parseMessages(self):
        """parse input buffer for all complete messages"""
        
        if not self.parserSynchronized:
            if not self._resynchronizeParser():
                # false if we empty the input buffer
                return None
        
        while True:
            # Check that buffer has enough bytes to use
            if len(self.inputBuffer) < 2:
                #self._log("buffer reached low watermark")
                return None
            
            # We expect 0x7e at the head of the buffer
            if self.inputBuffer[0] != 0x7e:
                # failed assertion; we are not synchronized anymore
                #self._log("synchronization lost")
                if not self._resynchronizeParser():
                    # false if we empty the input buffer
                    return None
            
            # Look to see if we have an ending 0x7e marker yet
            try:
                i = self.inputBuffer.index(chr(0x7e), 1)
            except ValueError:
                # no end marker found yet
                #self._log("no end marker found; leaving parser for now")
                return None
            
            # Extract byte message without markers and delete bytes from buffer
            msg = self.inputBuffer[1:i]
            del(self.inputBuffer[0:i+1])
            
            # Decode the received message
            # Returns whatever was decoded, either None or a message number
            return self._decodeMessage(msg)
        
        return None
    
    
    def _resynchronizeParser(self):
        """throw away bytes in buffer until empty or resynchronized
        Return:  true=resynchronized, false=buffer empty & not synced"""
        
        self.parserSynchronized = False
        
        while True:
            if len(self.inputBuffer) < 2:
                #self._log("buffer reached low watermark during sync")
                return False
            
            # found end of a message and beginning of next
            if self.inputBuffer[0] == 0x7e and self.inputBuffer[1] == 0x7e:
                # remove end marker from previous message
                del(self.inputBuffer[0:1])
                self.parserSynchronized = True
                #self._log("parser is synchronized (end:start)")
                return True
            
            if self.inputBuffer[0] == 0x7e:
                self.parserSynchronized = True
                #self._log("parser is synchronized (start)")
                return True
            
            # remove everything up to first 0x7e or end of buffer
            try:
                i = self.inputBuffer.index(chr(0x7e))
                #self._log("removing leading bytes before marker")
            except ValueError:
                # did not find 0x7e, so blank the whole buffer
                i = len(self.inputBuffer)
                #self._log("removing all bytes in buffer since no markers")
            #self._log('inputBuffer[0:%d]=' % (len(self.inputBuffer)) +str(self.inputBuffer)[:+32])
            del(self.inputBuffer[0:i])
        
        raise Exception("_resynchronizeParser: unexpected reached end")

    
    def _decodeMessage(self, escapedMessage):
        """
        decode one GDL90 message without the start/end markers
        returns None or othe message number that was processed
        """
        
        rawMsg = self._unescape(escapedMessage)
        if len(rawMsg) < 5:
            return None
        msg = rawMsg[:-2]
        crc = rawMsg[-2:]
        crcValid = crcCheck(msg, crc)
        
        m = messages.messageToObject(msg)
        if not m:
            return None
        
        if m.MsgType == 'Heartbeat':
            # MsgType StatusByte1 StatusByte2 TimeStamp MessageCounts
            logging.info('MSG00: s1=%02x, s2=%02x, ts=%02x' % (m.StatusByte1, m.StatusByte2, m.TimeStamp))

            # TimeStamp is the number of seconds since midnight, UTC
            self.seconds_since_midnight = int(m.TimeStamp)
            self.current_datetime = datetime.datetime.combine(
                datetime.date.today(),
                datetime.time(0, 0, 0),
            ) + datetime.timedelta(seconds=int(m.TimeStamp))

            self.gpsAge += 1
            return 0  # message 0 received
        
        elif m.MsgType == 'OwnershipReport':
            # MsgType Status Type Address Latitude Longitude Altitude Misc NavIntegrityCat NavAccuracyCat 
            # HVelocity VVelocity TrackHeading EmitterCat CallSign Code

            logging.info('MSG 10: %0.7f %0.7f %d %d %d' % (m.Latitude, m.Longitude, m.HVelocity, m.Altitude, m.TrackHeading))

            self.latitude = m.Latitude
            self.longitude = m.Longitude
            self.course = m.TrackHeading        
            self.vertical_speed = m.VVelocity   # fpm
            self.speed = m.HVelocity            # knots
            self.pressure_altitude = m.Altitude 
            self.nic = m.NavIntegrityCat        # >= 8 is probably great for us
            self.nac = m.NavAccuracyCat         # >= 8 is probably great for us

            return 10 # message number 10

        
        elif m.MsgType == 'OwnershipGeometricAltitude':
            # MsgType Altitude VerticalMetrics
            logging.info('MSG11: %d %04xh' % (m.Altitude, m.VerticalMetrics))
            self.altitude = m.Altitude

            return 11 # message number 11

        
        # This message does not seem to be sent by my NGT-9000 or stratux
        # Not sure what that's all about... would be super userful to have a 
        # real clock.
        """
        elif m.MsgType == 'GpsTime':

            if not self.gpsTimeReceived:
                self.gpsTimeReceived = True
                utcTime = datetime.time(m.Hour, m.Minute, 0)
                self.currtime = datetime.datetime.combine(self.dayStart, utcTime)
            else:
                # correct time slips and move clock forward if necessary
                if self.currtime.hour < m.Hour or self.currtime.minute < m.Minute:
                    utcTime = datetime.time(m.Hour, m.Minute, 0)
                    self.currtime = datetime.datetime.combine(self.currtime, utcTime)
            
            print 'MSG101: %02d:%02d UTC (waas = %s)' % (m.Hour, m.Minute, m.Waas)
        """

        # Traffic reporting code has been ripped out, we don't need it

        return None
    
    
    def _unescape(self, msg):
        """unescape 0x7e and 0x7d characters in coded message"""
        msgNew = bytearray()
        escapeValue = 0x7d
        foundEscapeChar = False
        while True:
            try:
                i = msg.index(chr(escapeValue))
                foundEscapeChar = True
                msgNew.extend(msg[0:i]); # everything up to the escape character
                
                # this will throw an exception if nothing follows the escape
                escapedValue = msg[i+1] ^ 0x20
                msgNew.append(chr(escapedValue)); # escaped value
                del(msg[0:i+2]); # remove prefix bytes, escape, and escaped value
                
            except (ValueError, IndexError):
                # no more escape characters
                if foundEscapeChar:
                    msgNew.extend(msg)
                    return msgNew
                else:
                    return msg
        
        raise Exception("_unescape: unexpected reached end")
    
    
    def _messageHex(self, msg, prefix="", suffix="", maxbytes=32, breakint=4):
        """prints the hex contents of a message"""
        s = ""
        numbytes=len(msg)
        if numbytes > maxbytes:  numbytes=maxbytes
        for i in range(numbytes):
            s += "%02x" % (msg[i])
            if ((i+1) % breakint) == 0:
                s += " "
        return "%s%s%s" % (prefix, s.strip(), suffix)
    
