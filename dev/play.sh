#!/bin/bash

raspi-gpio set 18 op a5

raspi-gpio set 23 op
raspi-gpio set 23 dh
sleep .4
play /tmp/output.wav
raspi-gpio set 23 dl