#
# Example of BME280 Sensor. Using I2C at P9, P10
#
# https://github.com/robert-hh/BME280 

from machine import I2C
from bme280 import *
from utime import sleep

i2c=I2C(0)
print (i2c. scan ())

bme280 = BME280(i2c=i2c)
result = [0]*3
while True:
    print(bme280.values)

    
    bme280.read_raw_data(result)

    print ("raw data ", result)

    temp, pressure, humidity = bme280.read_compensated_data()
    print ("Temp: ", temp)
    print ("Humidity: ", humidity)
    print ("Pressure: ", pressure)

    sleep(10)
