import afsk
import audiogen
from bitarray import bitarray
import RPi.GPIO as GPIO
import time
from afsk.ax25 import UI


GPIO.setmode(GPIO.BCM)

radio_tx_pin = 23
green_led = 24
yellow_led = 25

GPIO.setup(green_led, GPIO.OUT)
GPIO.setup(yellow_led, GPIO.OUT)
GPIO.setup(radio_tx_pin, GPIO.OUT)

GPIO.output(green_led, GPIO.HIGH)
GPIO.output(yellow_led, GPIO.HIGH)

packet = "KD9KEO-9>APZ001,WIDE1-1,WIDE2-2:/235619h4304.95N/08912.63W>000/003/A=000859/Pa=98573/Rh=69.98/Ti=23.43 Tracksoar v1.2"

bits = bitarray(endian="little")
bits.frombytes("".join([packet]))

audio = afsk.encode(bits)

packet = UI(
        destination="APZ999",
        source="KD9KEO-9",
        info="/235619h4304.95N/08912.63W>000/003/A=000859 hooooly shit it works",
        digipeaters="WIDE1-1,WIDE2-2".split(b','),
)

audio = afsk.encode(packet.unparse())


#GPIO.output(radio_tx_pin, GPIO.HIGH)
#time.sleep(.4)
#audiogen.sampler.play(audio, blocking=True)
with open("/tmp/output.wav", "w") as f:
    audiogen.sampler.write_wav(f, audio)
#GPIO.output(radio_tx_pin, GPIO.LOW)


GPIO.output(green_led, GPIO.LOW)
GPIO.output(yellow_led, GPIO.LOW)
GPIO.cleanup()