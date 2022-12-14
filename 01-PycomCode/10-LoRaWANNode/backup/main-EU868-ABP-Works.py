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
    --OTAA Node example-- I modified for ABP Node  as per LoRaWAN EU868 regional specification
    - compatible with the LoPy Nano Gateway and all other LoraWAN gateways
    - tested works with a LoRaServer and TTN servers
"""

from network import LoRa
import socket
import binascii
import struct
import time

LORA_CHANNEL = 1 # zero = random
LORA_NODE_DR = 3
'''
    utility function to setup the lora channels
'''
def prepare_channels(lora, channel, data_rate):
    EU868_FREQUENCIES = [
        { "chan": 1, "fq": "868100000" },
        { "chan": 2, "fq": "868300000" },
        { "chan": 3, "fq": "868500000" },
        { "chan": 4, "fq": "867100000" },
        { "chan": 5, "fq": "867300000" },
        { "chan": 6, "fq": "867500000" },
        { "chan": 7, "fq": "867700000" },
        { "chan": 8, "fq": "867900000" },
    ]
    if not channel in range(0, 9):
        raise RuntimeError("channels should be in 0-8 for EU868")

    if channel == 0:
        import  uos
        channel = (struct.unpack('B',uos.urandom(1))[0] % 7) + 1

    upstream = (item for item in EU868_FREQUENCIES if item["chan"] == channel).__next__()

    # set the 3 default channels to the same frequency
    lora.add_channel(0, frequency=int(upstream.get('fq')), dr_min=0, dr_max=5)
    lora.add_channel(1, frequency=int(upstream.get('fq')), dr_min=0, dr_max=5)
    lora.add_channel(2, frequency=int(upstream.get('fq')), dr_min=0, dr_max=5)

    for i in range(3, 16):
        lora.remove_channel(i)

    return lora

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

lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868) #, device_class=LoRa.CLASS_C)

# create an ABP authentication params
dev_addr = struct.unpack(">l", binascii.unhexlify('2601147D'))[0]
nwk_swkey = binascii.unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
app_swkey = binascii.unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')

prepare_channels(lora, LORA_CHANNEL, LORA_NODE_DR)

# join a network using ABP
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey), timeout=0,  dr=LORA_NODE_DR) # DR is 2 in v1.1rb but 0 worked for ne

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

# msg are confirmed at the FMS level
lora_socket.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, 0)

# make the socket non blocking y default
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
