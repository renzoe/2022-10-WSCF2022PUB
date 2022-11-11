import pycom
import time

from network import WLAN
import machine


import ubinascii


wlan = WLAN(mode=WLAN.STA)


#pycom.heartbeat(False)

print("Hello World!")

nets = wlan.scan()
print (nets)

# In this example we connect to a network, but for our workshop we will NOT connect ; 
# workshop's SSID : "wscf2022" (we can get info of RSSI using "net.rssi" on the scan result )
for net in nets:
    print(net.ssid)
    if net.ssid == 'wifing':
        print('Network found!')
        wlan.connect(net.ssid, auth=(net.sec, 'wifing-pub'), timeout=5000)
        while not wlan.isconnected():
            machine.idle() # save power while waiting
        print('WLAN connection succeeded!')
        break

#https://forum.pycom.io/topic/1816/any-way-to-get-rssi-of-existing-connection-without-scan/4
while True:
    #print (wlan.status('rssi')) # AttributeError: 'WLAN' object has no attribute 'status'
    print (wlan.joined_ap_info()) #(bssid=b'0|\xb2\xb3H\x86', ssid='KittyNet-Orange', primary_chn=1, rssi=-70, auth=3, standard=1) 
    time.sleep(5)
