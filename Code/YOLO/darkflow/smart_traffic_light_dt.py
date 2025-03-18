# LAG
# NO. OF VEHICLES IN SIGNAL CLASS
# stops not used
# DISTRIBUTION
# BUS TOUCHING ON TURNS
# Distribution using python class

# *** IMAGE XY COOD IS TOP LEFT
import random
import math
import time
import threading
# from vehicle_detection import detection
import pygame
import sys
import os
import requests
from io import BytesIO
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse

# Setup argparse
parser = argparse.ArgumentParser(description="Simulation with optional commands.")
parser.add_argument("--show-count", action="store_true", help="Show vehicle count per direction.")
parser.add_argument("--show-crossed", action="store_true", help="Show vehicle crossed per direction.")
parser.add_argument("--weather-update", action="store_true", help="Integrate real time with weather data.")
parser.add_argument("--atcs-update", action="store_true", help="Integrate real time with atcs data.")
parser.add_argument("--traffic-simulation", action="store_true", help="Simulate traffic light management.")
args = parser.parse_args()


# OpenWeather API Configuration
API_KEY = "4214fafba3bc355f824d5de9edbd3515"  # Ganti dengan API Key Anda
CITY = "Bandung"
WEATHER_ICON_URL = "http://openweathermap.org/img/wn/"

# Variabel global untuk ikon cuaca dan data cuaca
weather_data = {"icon": None, "description": "", "temp": 0, "city":"", "main":""}
weather_icon = None
icon_code = ''

DB_CONFIG = {
    'dbname': 'stl',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

# Default values of signal times
defaultRed = 5
defaultYellow = 2
defaultGreen = 5
defaultMinimum = 10
defaultMaximum = 60

signals = []
noOfSignals = 4
simTime = 600       # change this to change time of simulation
timeElapsed = 0

currentGreen = 0   # Indicates which signal is green
nextGreen = (currentGreen+1)%noOfSignals
currentYellow = 0   # Indicates whether yellow signal is on or off

green_background = (0, 255, 0)
yellow_background = (255, 255, 0)
red_background = (255, 0, 0)

# Average times for vehicles to pass the intersection
carTime = 2
bikeTime = 1
rickshawTime = 2.25
busTime = 2.5
truckTime = 2.5

# Count of cars at a traffic signal
noOfCars = 0
noOfBikes = 0
noOfBuses =0
noOfTrucks = 0
noOfRickshaws = 0
noOfLanes = 2
noOfMaxVehicleInDirection = {'car1': 0,'bus1': 0,'truck1': 0,'rickshaw1': 0,'bike1': 0}

# Red signal time at which cars will be detected at a signal
detectionTime = 0

speeds = {'car1':2.25, 'bus1':1.8, 'truck1':1.8, 'rickshaw1':2, 'bike1':2.5}  # average speeds of vehicles

# Coordinates of start
x = {'right':[20,20,20], 'down':[755,727,697], 'left':[1300,1300,1300], 'up':[602,627,657]}
y = {'right':[348,370,398], 'down':[20,20,20], 'left':[498,466,436], 'up':[760,760,760]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0, 'appear':{'car1':0,'bus1':0, 'truck1':0, 'rickshaw1':0, 'bike1':0}}, 'down': {0:[], 1:[], 2:[], 'crossed':0, 'appear':{'car1':0,'bus1':0, 'truck1':0, 'rickshaw1':0, 'bike1':0}}, 'left': {0:[], 1:[], 2:[], 'crossed':0, 'appear':{'car1':0,'bus1':0, 'truck1':0, 'rickshaw1':0, 'bike1':0}}, 'up': {0:[], 1:[], 2:[], 'crossed':0, 'appear':{'car1':0,'bus1':0, 'truck1':0, 'rickshaw1':0, 'bike1':0}}}
vehicleTypes = {0:'car1', 1:'bus1', 2:'truck1', 3:'rickshaw1', 4:'bike1'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}
viewDirection = {'right':'left', 'left':'right', 'down':'up', 'up':'down'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(535,320),(730,285),(770,480),(578,510)]
signalTimerCoods = [(570,300),(790,300),(795,550),(555,550)]
vehicleCrossedCoods = [(1150,620),(1150,650),(1150,680),(1150,710)]
vehicleCountCoods = [(980,620),(980,650),(980,680),(980,710)]
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCrossedTexts = ["0", "0", "0", "0"]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stops = {'right': [580,580,580], 'down': [320,320,320], 'left': [810,810,810], 'up': [545,545,545]}

mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
rotationAngle = 3

# Gap between vehicles
gap = 15    # stopping gap
gap2 = 15   # moving gap

# Setup Table
name_db = "stl"
user_db = "postgres"
password_db = "postgres"
host_db = "localhost"
port_db = "5432"

pygame.init()
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "30"
        self.totalGreenTime = 0

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = choose_path(direction, vehicleClass)
        self.path = path
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        if(direction=='right'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):    # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().width - gap         # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap
            else:
                self.stop = defaultStop[direction]
            # Set new starting and stopping coordinate
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='left'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().width + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().width + gap
            x[direction][lane] += temp
            stops[direction][lane] += temp
        elif(direction=='down'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect().height - gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] -= temp
            stops[direction][lane] -= temp
        elif(direction=='up'):
            if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].currentImage.get_rect().height + gap
            else:
                self.stop = defaultStop[direction]
            temp = self.currentImage.get_rect().height + gap
            y[direction][lane] += temp
            stops[direction][lane] += temp

        simulation.add(self)
        vehicles[direction]['appear'][vehicleClass] += 1

    def render(self, screen):
        screen.blit(self.currentImage, (self.x, self.y))

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.currentImage.get_rect().width>stopLines[self.direction]):   # if the image has crossed stop line now
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                vehicles[self.direction]['appear'][self.vehicleClass] -= 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x+self.currentImage.get_rect().width<mid[self.direction]['x']):
                    if((self.x+self.currentImage.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.x += self.speed
                else:
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 2
                        self.y += 1.8
                        if(self.rotateAngle==90):
                            self.turned = 1
                            # path = "images/" + directionNumbers[((self.direction_number+1)%noOfSignals)] + "/" + self.vehicleClass + ".png"
                            # self.x = mid[self.direction]['x']
                            # self.y = mid[self.direction]['y']
                            # self.image = pygame.image.load(path)
                    else:
                        if(self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2)):
                            self.y += self.speed
            else:
                if((self.x+self.currentImage.get_rect().width<=self.stop or self.crossed == 1 or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.currentImage.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x += self.speed  # move the vehicle



        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.currentImage.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                vehicles[self.direction]['appear'][self.vehicleClass] -= 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y+self.currentImage.get_rect().height<mid[self.direction]['y']):
                    if((self.y+self.currentImage.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.y += self.speed
                else:
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 2.5
                        self.y += 2
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or self.y<(vehicles[self.direction][self.lane][self.index-1].y - gap2)):
                            self.x -= self.speed
            else:
                if((self.y+self.currentImage.get_rect().height<=self.stop or self.crossed == 1 or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.currentImage.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):
                    self.y += self.speed

        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                vehicles[self.direction]['appear'][self.vehicleClass] -= 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.x>mid[self.direction]['x']):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.x -= self.speed
                else:
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if(self.rotateAngle==90):
                            self.turned = 1
                            # path = "images/" + directionNumbers[((self.direction_number+1)%noOfSignals)] + "/" + self.vehicleClass + ".png"
                            # self.x = mid[self.direction]['x']
                            # self.y = mid[self.direction]['y']
                            # self.currentImage = pygame.image.load(path)
                    else:
                        if(self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or self.x>(vehicles[self.direction][self.lane][self.index-1].x + gap2)):
                            self.y -= self.speed
            else:
                if((self.x>=self.stop or self.crossed == 1 or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x -= self.speed  # move the vehicle
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                vehicles[self.direction]['appear'][self.vehicleClass] -= 1
            if(self.willTurn==1):
                if(self.crossed==0 or self.y>mid[self.direction]['y']):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height +  gap2) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                        self.y -= self.speed
                else:
                    if(self.turned==0):
                        self.rotateAngle += rotationAngle
                        self.currentImage = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                        self.x += 1
                        self.y -= 1
                        if(self.rotateAngle==90):
                            self.turned = 1
                    else:
                        if(self.index==0 or self.x<(vehicles[self.direction][self.lane][self.index-1].x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width - gap2) or self.y>(vehicles[self.direction][self.lane][self.index-1].y + gap2)):
                            self.x += self.speed
            else:
                if((self.y>=self.stop or self.crossed == 1 or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height + gap2) or (vehicles[self.direction][self.lane][self.index-1].turned==1))):
                    self.y -= self.speed


def choose_path(direction, vehicleClass):
    # Definisikan path untuk car dan bus
    if vehicleClass in ['car1']:
        path1 = "images/" + direction + "/car1.png"
        path2 = "images/" + direction + "/car2.png"
        possible_paths = [path1, path2]  # Dua path untuk car
        chosen_path = random.choice(possible_paths)
        return chosen_path
    elif vehicleClass in ['bus1']:
        path1 = "images/" + direction + "/bus1.png"
        path2 = "images/" + direction + "/bus2.png"
        possible_paths = [path1, path2]  # Dua path untuk bus
        chosen_path = random.choice(possible_paths)
        return chosen_path
    else:
        return "images/" + direction + "/" + vehicleClass + ".png"  # Path default untuk kendaraan lainnya

def removeCrossedVehicles():
    global vehicles
    for direction in vehicles.keys():
        for lane in range(3):  # Assume maximum 3 lanes
            # Hapus kendaraan yang telah melewati batas
            vehicles[direction][lane] = [
                vehicle for vehicle in vehicles[direction][lane] if not hasCrossed(vehicle)
            ]
            # Perbarui indeks kendaraan yang tersisa
            for idx, vehicle in enumerate(vehicles[direction][lane]):
                vehicle.index = idx

def hasCrossed(vehicle):
    # Define conditions for when a vehicle has crossed
    if vehicle.direction == 'right':
        return vehicle.x > 1400  # Rightward vehicles move off screen at x > 1400
    elif vehicle.direction == 'down':
        return vehicle.y > 800  # Downward vehicles move off screen at y > 800
    elif vehicle.direction == 'left':
        return vehicle.x < 0  # Leftward vehicles move off screen at x < 0
    elif vehicle.direction == 'up':
        return vehicle.y < 0  # Upward vehicles move off screen at y < 0
    return False


# Initialization of signals with default values
def initialize():
    global detectionTime
    data = getDataTrafficLight("traffic_light")
    if data:
        # red_time = data.get('red_light', defaultRed)
        yellow_time = data.get('yellow_light', defaultYellow)
        green_time = data.get('green_light', defaultGreen)

    # Inisialisasi TrafficSignal dengan data dari database
    ts1 = TrafficSignal(0, yellow_time, green_time, defaultMinimum, defaultMaximum)
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.yellow + ts1.green, yellow_time, green_time, defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(ts2.red + ts2.yellow + ts2.green, yellow_time, green_time, defaultMinimum, defaultMaximum)
    signals.append(ts3)
    ts4 = TrafficSignal(ts3.red + ts3.yellow + ts3.green, yellow_time, green_time, defaultMinimum, defaultMaximum)
    signals.append(ts4)
    repeat()

# Set time according to formula
def setTime():
    global noOfCars, noOfBikes, noOfBuses, noOfTrucks, noOfRickshaws, noOfLanes
    global carTime, busTime, truckTime, rickshawTime, bikeTime

    noOfCars, noOfBuses, noOfTrucks, noOfRickshaws, noOfBikes = 0,0,0,0,0
    for j in range(len(vehicles[directionNumbers[nextGreen]][0])):
        vehicle = vehicles[directionNumbers[nextGreen]][0][j]
        if(vehicle.crossed==0):
            vclass = vehicle.vehicleClass
            # print(vclass)
            noOfBikes += 1
    for i in range(1,3):
        for j in range(len(vehicles[directionNumbers[nextGreen]][i])):
            vehicle = vehicles[directionNumbers[nextGreen]][i][j]
            if(vehicle.crossed==0):
                vclass = vehicle.vehicleClass
                # print(vclass)
                if(vclass=='car1'):
                    noOfCars += 1
                elif(vclass=='bus1'):
                    noOfBuses += 1
                elif(vclass=='truck1'):
                    noOfTrucks += 1
                elif(vclass=='rickshaw1'):
                    noOfRickshaws += 1

    greenTime = math.ceil(((noOfCars*carTime) + (noOfRickshaws*rickshawTime) + (noOfBuses*busTime) + (noOfTrucks*truckTime)+ (noOfBikes*bikeTime))/(noOfLanes+1))


    if weather_data['main'] in ['Rain', 'Thunderstorm', 'Drizzle', 'Fog']:
        greenTime -= 5

    # if sum(vehicles[directionNumbers[nextGreen]]['appear'].values()) > 15:
    #     greenTime = adjustTime(greenTime, 10)
    # elif sum(vehicles[directionNumbers[nextGreen]]['appear'].values()) < 7:
    #     greenTime = adjustTime(greenTime, -5)
    # else:
    #     greenTime = adjustTime(greenTime, 0)
    greenTime = adjustTime(greenTime, 0)

    signals[(currentGreen+1)%(noOfSignals)].green = greenTime

def adjustTime(signalTime, addTime):

    if (signalTime + addTime) <= 3:
        return 5 if signalTime <= 5 else signalTime
    else:
        return signalTime + addTime

def repeat():
    global currentGreen, currentYellow, nextGreen, noOfMaxVehicleInDirection, detectionTime
    data2 = getDataTotalVehicle("vehicle")
    if data2:
        noOfMaxVehicleInDirection['car1'] =  data2.get('car_count', 10)
        noOfMaxVehicleInDirection['bike1'] =  data2.get('bike_count', 10)
        noOfMaxVehicleInDirection['bus1'] =  data2.get('bus_count', 10)
        noOfMaxVehicleInDirection['truck1'] =  data2.get('truck_count', 10)
        noOfMaxVehicleInDirection['rickshaw1'] =  data2.get('rickshaw_count', 10)

    while(signals[currentGreen].green>0):   # while the timer of current green signal is not zero
        printStatus()
        updateValues()
        if(signals[(currentGreen+1)%(noOfSignals)].red==detectionTime and args.traffic_simulation):    # set time of next green signal
            setTime()
        time.sleep(1)
    currentYellow = 1   # set yellow signal on
    vehicleCountTexts[currentGreen] = "0"
    # reset stop coordinates of lanes and vehicles
    for i in range(0,3):
        stops[directionNumbers[currentGreen]][i] = defaultStop[directionNumbers[currentGreen]]
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while(signals[currentGreen].yellow>0):  # while the timer of current yellow signal is not zero
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0   # set yellow signal off

    # reset all signal times of current signal to default times
    data = getDataTrafficLight("traffic_light")
    if data:
        signals[currentGreen].green = data.get('green_light', defaultGreen)
        signals[currentGreen].yellow = data.get('yellow_light', defaultYellow)
        detectionTime = signals[currentGreen].yellow + 1

    currentGreen = nextGreen # set next signal as green signal
    nextGreen = (currentGreen+1)%noOfSignals    # set next green signal
    signals[nextGreen].red = signals[currentGreen].yellow+signals[currentGreen].green    # set the red time of next to next signal as (yellow time + green time) of next signal
    next2Green = (nextGreen+1)%noOfSignals
    signals[next2Green].red = signals[nextGreen].red + signals[nextGreen].yellow + signals[nextGreen].green
    next3Green = (next2Green+1)%noOfSignals
    signals[next3Green].red = signals[next2Green].red + signals[next2Green].yellow + signals[next2Green].green
    repeat()

# Print the signal timers on cmd
def printStatus():
    pass
	# for i in range(0, noOfSignals):
	# 	if(i==currentGreen):
	# 		if(currentYellow==0):
	# 			print("GREEN TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
	# 		else:
	# 			print("YELLOW TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
	# 	else:
	# 		print("RED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
	# print()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
                signals[i].totalGreenTime+=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

# Generating vehicles in the simulation
def generateVehicles():
    global noOfMaxVehicleInDirection
    while(True):
        vehicle_type = random.randint(0,4)
        if(vehicle_type==4):
            lane_number = 0
        else:
            lane_number = random.randint(0,1) + 1
        will_turn = 0
        if(lane_number==2):
            temp = random.randint(0,4)
            if(temp<=2):
                will_turn = 1
            elif(temp>2):
                will_turn = 0
        temp = random.randint(0,999)
        direction_number = 0
        a = [400,800,900,1000]
        if(temp<a[0]):
            direction_number = 0
        elif(temp<a[1]):
            direction_number = 1
        elif(temp<a[2]):
            direction_number = 2
        elif(temp<a[3]):
            direction_number = 3

        if sum(vehicles[directionNumbers[direction_number]]['appear'].values()) < sum(noOfMaxVehicleInDirection.values()):
            if vehicles[directionNumbers[direction_number]]['appear'][vehicleTypes[vehicle_type]] < noOfMaxVehicleInDirection[vehicleTypes[vehicle_type]]:
                Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(0.30)

def simulationTime():
    global timeElapsed, simTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simTime):
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')
            for i in range(noOfSignals):
                print('Lane',i+1,':',vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']
            print('Total vehicles passed: ',totalVehicles)
            print('Total time passed: ',timeElapsed)
            print('No. of vehicles passed per unit time: ',(float(totalVehicles)/float(timeElapsed)))
            os._exit(1)

def getDataTrafficLight(table_name):
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(**DB_CONFIG)

        # Create a cursor
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Execute the SQL query
        query = f"SELECT * FROM {table_name} order by id desc limit 1;"
        cursor.execute(query)

        # Fetch all rows
        results = cursor.fetchall()

        # Return results
        return results[0]

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()

def getDataTotalVehicle(table_name):
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(**DB_CONFIG)

        # Create a cursor
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Execute the SQL query
        query = f"select coalesce(car_count,0) as car_count, coalesce(bus_count,0) as bus_count, coalesce(truck_count,0) as truck_count, coalesce(bike_count,0) as bike_count, coalesce(rickshaw_count,0) as rickshaw_count from {table_name} order by id desc limit 1;"
        cursor.execute(query)

        # Fetch all rows
        results = cursor.fetchall()

        # Return results
        return results[0]

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()

def updateSignalTimes():
    global signals, currentGreen, currentYellow
    while True:
        # Ambil data terbaru dari database
        data = getDataTrafficLight("traffic_light")
        if data:
            # Update nilai red, yellow, dan green berdasarkan data dari database
            for i, signal in enumerate(signals):
                # signal.red = data.get('red_light', signal.red)  # Gunakan nilai dari DB, atau pertahankan nilai sebelumnya
                signal.yellow = data.get('yellow_light', signal.yellow)
                signal.green = data.get('green_light', signal.green)
        time.sleep(60)  # Update setiap 1 menit


# Fungsi untuk mendapatkan data cuaca
def get_openweather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        main = data["weather"][0]["main"]
        icon_code = data["weather"][0]["icon"]
        description = data["weather"][0]["description"]
        temp = data['main']['temp']
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        city = data['name']
        lon = data['coord']['lon']
        lat = data['coord']['lat']

        insert_openweather_data(main, icon_code, description, temp, pressure, humidity, wind_speed, city, lon, lat)
        # icon_response = requests.get(f"{WEATHER_ICON_URL}{icon_code}@2x.png")

        # if icon_response.status_code == 200:
        #     icon_image = BytesIO(icon_response.content)
        #     current_weather_icon = pygame.image.load(icon_image, 'weather_icon')

    else:
        print("Gagal mengambil data cuaca")
        # return "Clear"  # Default jika gagal

# Fungsi untuk mendapatkan data atcs
def get_atcsspdago():
    url = f"https://c7f7d465-72e5-46ba-a18d-0a78d95a0128.mock.pstmn.io/atcs-spdago"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        green_light = data["green_light"]
        yellow_light = data["yellow_light"]

        insert_atcsspdago_data(green_light, yellow_light)

    else:
        print("Gagal mengambil data atcs")


def insert_openweather_data(main, icon, description, temp, pressure, humidity, wind_speed, city, lon, lat):
    try:
        # Koneksi ke database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query SQL untuk menyisipkan data
        query = """
            INSERT INTO weather (main, icon, description, temp, pressure, humidity, wind_speed, city, lon, lat, created_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        """
        values = (main, icon, description, temp, pressure, humidity, wind_speed, city, lon, lat)

        # Eksekusi query
        cursor.execute(query, values)
        connection.commit()

        print(f"Weather data inserted successfully: {values}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def insert_atcsspdago_data(green_light, yellow_light):
    try:
        # Koneksi ke database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query SQL untuk menyisipkan data
        query = """
            INSERT INTO traffic_light (green_light, yellow_light, created_date)
            VALUES (%s, %s, now())
        """
        values = (green_light, yellow_light)

        # Eksekusi query
        cursor.execute(query, values)
        connection.commit()

        print(f"Traffic light data inserted successfully: {values}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

# Thread untuk memperbarui cuaca secara periodik
def update_weather_periodically():
    while True:
        get_openweather()
        time.sleep(600)

def update_atcsspdago_periodically():
    while True:
        get_atcsspdago()
        time.sleep(60)

def getDataWeather(table_name):
    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(**DB_CONFIG)

        # Create a cursor
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        # Execute the SQL query
        query = f"SELECT * FROM {table_name} order by id desc limit 1;"
        cursor.execute(query)

        # Fetch all rows
        results = cursor.fetchall()

        # Return results
        return results[0]

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        if connection:
            cursor.close()
            connection.close()

def load_weather_icon(icon_code):
    try:
        # URL ikon cuaca
        url = f"{WEATHER_ICON_URL}{icon_code}@2x.png"
        response = requests.get(url)

        if response.status_code == 200:
            icon_image = pygame.image.load(BytesIO(response.content), 'weather_icon')
            return icon_image
        else:
            print(f"Failed to load weather icon: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error loading weather icon: {e}")
        return None

def update_weather_data():
    global weather_data, weather_icon, icon_code

    while True:
        # Ambil data terbaru dari database
        data = getDataWeather("weather")
        if data:
            try:
                # Perbarui data cuaca global
                weather_data["icon"] = data["icon"]
                weather_data["description"] = data["description"]
                weather_data["temp"] = data["temp"]
                weather_data["city"] = data["city"]
                weather_data["main"] = data["main"]

                # Unduh ikon cuaca terbaru
                if weather_data["icon"]:
                    if icon_code != weather_data["icon"]:
                        icon_code = weather_data["icon"]
                        weather_icon = load_weather_icon(icon_code)
            except Exception as e:
                print(f"Error updating weather data: {e}")

        # Tunggu 5 detik sebelum pembaruan berikutnya
        time.sleep(5)

def display_weather_icon(screen, font):
    global weather_data, weather_icon

    if weather_icon:
        # Tampilkan ikon cuaca
        screen.blit(weather_icon, (50, 50))  # Koordinat ikon cuaca

    # Tampilkan deskripsi cuaca dan suhu
    weather_text = font.render(f" {weather_data['temp']}°C, {weather_data['city']}: {weather_data['description'].title()}", True, (0, 0, 0), (255, 255, 255))
    screen.blit(weather_text, (150, 60))  # Koordinat deskripsi cuaca

class Main:
    thread4 = threading.Thread(name="simulationTime",target=simulationTime, args=())
    thread4.daemon = True
    thread4.start()

    thread2 = threading.Thread(name="initialization",target=initialize, args=())
    thread2.daemon = True
    thread2.start()

    thread5 = threading.Thread(name="updateSignalTimes", target=updateSignalTimes, args=())
    thread5.daemon = True
    thread5.start()

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/mod_int4.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SMART TRAFFIC LIGHT")

    redSignal = [
        pygame.image.load('images/signals/redright.png'),
        pygame.image.load('images/signals/reddown.png'),
        pygame.image.load('images/signals/redleft.png'),
        pygame.image.load('images/signals/redup.png')
    ]

    yellowSignal = [
        pygame.image.load('images/signals/yellowright.png'),
        pygame.image.load('images/signals/yellowdown.png'),
        pygame.image.load('images/signals/yellowleft.png'),
        pygame.image.load('images/signals/yellowup.png')
    ]

    greenSignal = [
        pygame.image.load('images/signals/greenright.png'),
        pygame.image.load('images/signals/greendown.png'),
        pygame.image.load('images/signals/greenleft.png'),
        pygame.image.load('images/signals/greenup.png')
    ]

    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread3.daemon = True
    thread3.start()

    if args.weather_update:
        thread_weather = threading.Thread(name="weatherUpdate", target=update_weather_periodically)
        thread_weather.daemon = True
        thread_weather.start()

    if args.atcs_update:
        thread_atcs = threading.Thread(name="atcsUpdate", target=update_atcsspdago_periodically)
        thread_atcs.daemon = True
        thread_atcs.start()

    thread_weather1 = threading.Thread(target=update_weather_data)
    thread_weather1.daemon = True  # Supaya thread berhenti saat program dihentikan
    thread_weather1.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))   # display background in simulation
        # Tampilkan ikon cuaca
        display_weather_icon(screen, font)
        for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
            if(i==currentGreen):
                if(currentYellow==1):
                    signals[i].signalText = signals[i].yellow
                    screen.blit((yellowSignal[i]), signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit((greenSignal[i]), signalCoods[i])
            else:
                if(signals[i].red>=0):
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"

                screen.blit((redSignal[i]), signalCoods[i])
        signalTexts = ["","","",""]

        # display signal timer and vehicle count
        for i in range(0,noOfSignals):
            if i == currentGreen:
                if currentYellow == 1:
                    bg_color = yellow_background
                else:
                    bg_color = green_background
            else:
                bg_color = red_background

            signalTexts[i] = font.render(str(signals[i].signalText), True, black, bg_color)
            screen.blit(signalTexts[i],signalTimerCoods[i])

            if args.show_crossed:
                displayText = f"{viewDirection[directionNumbers[i]]}: {vehicles[directionNumbers[i]]['crossed']}"
                vehicleCrossedTexts[i] = font.render(str(displayText), True, black, white)
                screen.blit(vehicleCrossedTexts[i],vehicleCrossedCoods[i])

            if args.show_count:
                displayText1 = f"{viewDirection[directionNumbers[i]]}: {sum(vehicles[directionNumbers[i]]['appear'].values())}"
                vehicleCountTexts[i] = font.render(str(displayText1), True, black, white)
                screen.blit(vehicleCountTexts[i],vehicleCountCoods[i])

        timeElapsedText = font.render(("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText,(1100,50))

        if args.show_crossed:
            vehicleCrossed = font.render(("Vehicle Crossed: "), True, black, white)
            screen.blit(vehicleCrossed,(1150,590))

        if args.show_count:
            vehicleCount = font.render(("Vehicle Count: "), True, black, white)
            screen.blit(vehicleCount,(980,590))

        # display the vehicles
        for vehicle in simulation:
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            # vehicle.render(screen)
            vehicle.move()
        pygame.display.update()

Main()


