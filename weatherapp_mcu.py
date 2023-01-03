from mqttclient import MQTTClient
import network
import sys
from ina219 import INA219
from machine import I2C, Pin
from board import SDA, SCL, LED
import time

#user inputs for number of data points and the interval between them
interval = float(input('Enter the interval (in seconds) between data collection:'))
points = float(input('How many data points should be collected:'))

#config GPIO pin 14
led = Pin(14, mode=Pin.OUT)

#i2c config
i2c = I2C(id=0, scl=Pin(SCL),sda=Pin(SDA), freq=100000)

shunt_res = 0.1 #circuit resistance?
ina = INA219(shunt_res, i2c)
ina.configure()

#mqtt session
session = 'nafees/ESP32/weatherapp'
BROKER = 'broker.mqttdashboard.com'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ip = wlan.ifconfig()[0]
if ip == '0.0.0.0':
    print('could not connect to WiFi')
    sys.exit()
else:
    print('connected successfully')

#connect to mqtt
mqtt = MQTTClient(BROKER, port=1883)
#grid = False;
i=0
topic = "{}/data".format(session)
while i<points:
    #120 sec delay
    time.sleep(interval)
    #solar panel current, power, and voltage
    solarV = ina.voltage()
    solarI = ina.current()/1000 #convert mA to amps
    solarP = (solarI * solarI * 330) + (solarI * 3)
    t_now = time.strftime('%H:%M')
    if solarI < 0.005:
        #drive current from ESP32
        led(1)
        gridI = 1
    else:
        led(0)
        gridI = 0
    # P = (i^2)* R
    # approximation for i, i = 0.01
    gridP = (gridI * 0.010 * 0.010 * 147) + (gridI * 0.010 * 3)
    i = i + 1
    print(i)
    data = "{:.4f},{:.5f},{:.5f},{:.5f},{:.5f},{}".format(solarV,solarI,solarP,gridI,gridP,t_now)
    mqtt.publish(topic, data)

mqtt.publish("{}/plot".format(session), "create the plot")