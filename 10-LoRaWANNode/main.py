#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

"""
    - ABP Node Example as per LoRaWAN EU868 regional specification
    - compatible with the LoPy Nano Gateway (and all other LoraWAN gateways)
    - tested works with a Chirpstack server
"""

from network import LoRa
import socket
import binascii
import struct
import time

# AU915 -- Uruguay
LORA_FREQUENCY = 915200000 # ver a que channel corresponde --> channel 0
LORA_NODE_DR = 3

'''
    call back for handling RX packets
'''
def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        if lora_socket is not None:
            frame, port = lora_socket.recvfrom(512) # longuest frame is +-220
            print(port, frame)
    if events & LoRa.TX_PACKET_EVENT:
        print("tx_time_on_air: {} ms @dr {}".format(lora.stats().tx_time_on_air, lora.stats().sftx))

'''
    Main operations: this is sample code for LoRaWAN on EU868
'''
# initialize LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Australia = LoRa.AU915
# Europe = LoRa.EU868
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AU915) #, device_class=LoRa.CLASS_C)

# create an ABP authentication params --  Check Chirpstack  enants/ChirpStack/Applications/{IOTAPP}/Devices/{IOTDEV} Activation (do not suport OTAA keyp)
# Here you should put the parameter from Chirpstack
dev_addr = struct.unpack(">l", binascii.unhexlify('2601147D'))[0]
nwk_swkey = binascii.unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
app_swkey = binascii.unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')

# remove all the channels
for channel in range(0, 72):
    lora.remove_channel(channel)

# set all channels to the same frequency (must be before sending the OTAA join request)
for channel in range(0, 72):
    lora.add_channel(channel, frequency=LORA_FREQUENCY, dr_min=0, dr_max=LORA_NODE_DR)



# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey), timeout=0,  dr=0) # Join uses specific DRs; but for APP will use the one in LORA_NODE_DR
#lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey)) # Maybe works with non-NanoGW, no need to setup LORA_NODE_DR

# wait until the module has joined the network
print('Over the air network activation ... ', end='')
while not lora.has_joined():
    time.sleep(2.5)
    print('.', end='')
print('')

# create a LoRa socket
lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
lora_socket.setsockopt(socket.SOL_LORA, socket.SO_DR, LORA_NODE_DR)

# msg are confirmed at the FMS level --> selecting non-confirmed type of messages (0== False)
lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, 0)

# make the socket non blocking by default
lora_socket.setblocking(False)

lora.callback(trigger=( LoRa.RX_PACKET_EVENT |
                        LoRa.TX_PACKET_EVENT |
                        LoRa.TX_FAILED_EVENT  ), handler=lora_cb)

time.sleep(4) # this timer is important and caused me some trouble ...

for i in range(0, 1000):
    pkt = struct.pack('>H', i)
    print('Sending:', pkt)
    lora_socket.send(pkt)
    time.sleep(30)
    #rx, port = lora_socket.recvfrom(256)
    #if rx:
    #    print('Received: {}, on port: {}'.format(rx, port))
    #time.sleep(26)
