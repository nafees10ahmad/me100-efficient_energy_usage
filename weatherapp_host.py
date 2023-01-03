import paho.mqtt.client as paho
import matplotlib.pyplot as plt

#predictions code start
#import libraries

import csv
import codecs
import urllib.request
import urllib.error
import sys
import datetime
import math


APIURL = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/'

ApiKey='GCATV5YN5MZ6QYFMYPZK2R2RC'
#use metric units
#units = 'metric'

#location
#hard coded:location = 'Berkeley'
location = input('Enter your location (city or zip code, case sensitive):')

#range of dates for data
#determine the current + end day from the datetime library

#hard coded: delta = 1
delta = int(input('Enter the forecasting period (0 gives only today''s weather):'))
today = str(datetime.date.today())
end = str(datetime.date.today() + datetime.timedelta(delta))

#data format
format = 'csv'

#format api query
#complete url
query = APIURL + location + '/' + today + '/' + end
#add search parameters
query += '?' + '&unitGroup=metric' + '&contentType=csv' + '&include=hours' + '&key=' + ApiKey + '&elements=location,datetime,solarradiation,solarenergy'

#run query
try:
    CSVraw = urllib.request.urlopen(query)
except urllib.error.HTTPError  as e:
    ErrorInfo= e.read().decode()
    print('Error code: ', e.code, ErrorInfo)
    sys.exit()
except  urllib.error.URLError as e:
    ErrorInfo= e.read().decode()
    print('Error code: ', e.code,ErrorInfo)
    sys.exit()


CSVclean = csv.reader(codecs.iterdecode(CSVraw, 'utf-8'))
RowIndex = 0
dtime = []
srad = []
senergy = []
expectedI = []

for Row in CSVclean:
    
    #placeholder- instead of print, calculate expected current for solar radiation/energy, then store in vector
    #once all rows are complete, send to MQTT (if necessary) for graphing
    #expectedI = row[2?] *conversion factor
    #print(Row[:])
    if RowIndex > 0:
        dtime.append(Row[0])
        srad.append(float(Row[1]))
        try:
            senergy.append(float(Row[2]))
        except:
            senergy.append(0)
        try:
            V = 1.1563*math.log(float(Row[1])) + 0.2232
            expectedI.append(V/330)
        except:
            expectedI.append(0)
    RowIndex += 1
#prediction code end

#session
session = "nafees/ESP32/weatherapp"
BROKER = "broker.mqttdashboard.com"
qos = 0 #?

#connect to MQTT broker
mqtt = paho.Client()
mqtt.connect(BROKER, port=1883)

#data vectors
solarV = []
solarI = []
solarP = []
gridI = []
gridP = []
t_vec = []
#totalP = []

#callbacks
# mqtt callbacks
def data(c, u, message):
    # extract data from MQTT message
    msg = message.payload.decode('ascii')
    # convert to vector of floats
    #f = [ float(x) for x in msg.split(',') ]
    f = []
    for x in msg.split(','):
        try:
            f.append(float(x))
        except:
            f.append(x)
    print(f)
    print("received", f)
    # append to data vectors, add more as needed
    solarV.append(f[0])
    solarI.append(f[1])
    solarP.append(f[2])
    gridI.append(f[3]*0.007)
    gridP.append(f[4])
    t_vec.append(f[5])
def plot(client, userdata, message):
    # customize this to match your data
    #fig, axs = plt.subplots(3,1)
    #plot 1- predicted hourly current from solar panel (plot points but leave them unconnected)
    plt.figure()
    plt.plot(dtime,expectedI, 'rs')
    plt.title('Predicted Hourly Solar Current (Amps)')
    
    plt.xlabel('Datetime')
    plt.ylabel('Current (Amps)')
    plt.xticks(rotation = 90)
    #plot 2- actual current from solar panel vs time
    plt.figure()
    plt.plot(t_vec,solarI)
    plt.title('Actual Solar Current')
    
    plt.xlabel('Datetime')
    plt.ylabel('Current (Amps)')
    #plot 3- actual usage (power consumption) vs solar power available (solar energy or radiation?)
    plt.figure()
    plt.plot(t_vec,solarP,label = 'Solar')
    plt.plot(t_vec,gridP,label = 'Grid')
    plt.title('Solar vs Grid Power Consumption')
    plt.legend()
    plt.ylabel('Power Consumption')
    plt.xlabel('Time')
    plt.show()
    #plt.xlabel('Datetime')
    #plt.ylabel('Power consumtion')
    sys.exit()
# subscribe to topics
data_topic = "{}/data".format(session, qos)
plot_topic = "{}/plot".format(session, qos)
mqtt.subscribe(data_topic)
mqtt.subscribe(plot_topic)
mqtt.message_callback_add(data_topic, data)
mqtt.message_callback_add(plot_topic, plot)
# wait for MQTT messages
# this function never returns
print("waiting for data ...")
mqtt.loop_forever()