# This code will connect to LoRaWAN and send one packet that contain several mesaures encoded in CayenneLPP

from network import LoRa
from network import WLAN
import socket
import binascii
import struct
import time
import cayenneLPP  # For  more info on this CayenneLPP lib see https://github.com/jojo-/py-cayenne-lpp

#LORA_FREQUENCY = 868100000
#LORA_NODE_DR = 3

# AU915 -- Uruguay
LORA_FREQUENCY = 915200000 # ver a que channel corresponde --> channel 0
LORA_NODE_DR = 3

'''
    call back for handling RX packets . Renzo: this is not necessary, just to do some post-processing
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
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AU915) #
#lora = LoRa(mode=LoRa.LORAWAN, adr=False, tx_retries=0, device_class=LoRa.CLASS_A)

# create an ABP authentication params --  Check Chirpstack  enants/ChirpStack/Applications/{IOTAPP}/Devices/{IOTDEV} Activation (do not suport OTAA keyp)
dev_addr = struct.unpack(">l", binascii.unhexlify('2601147D'))[0]
nwk_swkey = binascii.unhexlify('3C74F4F40CAEA021303BC24284FCF3AF')
app_swkey = binascii.unhexlify('0FFA7072CC6FF69A102A0F39BEB0880F')


# remove all the channels
for channel in range(0, 72):
    lora.remove_channel(channel)

# set all channels to the same frequency (must be before sending the OTAA join request)
for channel in range(0, 72):
    lora.add_channel(channel, frequency=LORA_FREQUENCY, dr_min=0, dr_max=LORA_NODE_DR)


# EU868 set the 3 default channels to the same frequency -- This is done because of a NanoGW limitations (not a problem with dragino)
#lora.add_channel(0, frequency=LORA_FREQUENCY, dr_min=0, dr_max=LORA_NODE_DR)
#lora.add_channel(1, frequency=LORA_FREQUENCY, dr_min=0, dr_max=LORA_NODE_DR)
#lora.add_channel(2, frequency=LORA_FREQUENCY, dr_min=0, dr_max=LORA_NODE_DR)

# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey), timeout=0,  dr=0) # Join uses specific DRs
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
#lora_socket.setblocking(True)

lora.callback(trigger=( LoRa.RX_PACKET_EVENT |
                        LoRa.TX_PACKET_EVENT |
                        LoRa.TX_FAILED_EVENT  ), handler=lora_cb)

time.sleep(4) # this timer is important and caused me some trouble ...


# creating Cayenne LPP packet
lpp = cayenneLPP.CayenneLPP(size = 100, sock = lora_socket)
wlan = WLAN(mode=WLAN.STA)

while True:
    nets = wlan.scan()
    for net in nets:
        if net.ssid == 'wscf2022':
            print(net.rssi)
            lpp.add_analog_input(net.rssi)
            lpp.send(reset_payload = True)
    
    time.sleep(30)

# This is dead code... a bad programming habit. But you have some CayenneLPP examples

# Creating some Cayenne LPP payloads and sending them
#lpp.add_analog_input(102.34)
#lpp.add_analog_input(-89.34, channel = 114)
#lpp.send(reset_payload = True)

#lpp.add_temperature(-11.0)
#lpp.add_temperature(54.3, channel = 118)
#lpp.send(reset_payload = True)

#lpp.add_relative_humidity(100.0)
#lpp.add_relative_humidity(0.0, channel = 119)
#lpp.send(reset_payload = True)

#lpp.add_gps(50.5434, 4.4069, 100.98)
#lpp.send(reset_payload = True)
