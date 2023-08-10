import random
import time
import threading
import pygame
import sys
import os
from tkinter import Tk
from tkinter import *
from tkinter import messagebox
import pedestrians as pd

#####################################################
# Default values of signal timers
defaultGreen = {0:10, 1:10, 2:10, 3:10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 4
currentGreen = 0   # Indicates which signal is green currently
nextGreen = (currentGreen+1)%noOfSignals    # Indicates which signal will turn green next
currentYellow = 0   # Indicates whether yellow signal is on or off 

speeds = {'car':1.25, 'bus':0.8, 'truck':0.8, 'bike':1.5}  # average speeds of vehicles

# Coordinates of vehicles' start
x = {'right':[0,0,0], 'down':[755,727,697], 'left':[1400,1400,1400], 'up':[602,627,657]}    
y = {'right':[348,370,398], 'down':[0,0,0], 'left':[498,466,436], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(560,210),(785,210),(795,570),(555,570)]
signalTimerCoods = [(560,190),(785,190),(795,658),(561,658)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 25    # stopping gap
movingGap = 25  # moving gap

# set allowed vehicle types here
allowedVehicleTypes = {'car': True, 'bus': True, 'truck': True, 'bike': True}
allowedVehicleTypesList = []
vehiclesTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
vehiclesNotTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
rotationAngle = 3
mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}
# set random or default green signal time here 
randomGreenSignalTimer = True
# set random green signal time range here 
randomGreenSignalTimerRange = [10,20]

timeElapsed = 0
simulationTime = 3000
timeElapsedCoods = (1100,50)
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCountCoods = [(480,210),(880,210),(880,550),(480,550)]

pygame.init()
simulation = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        
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
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)


        if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):   
            if(direction=='right'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                - vehicles[direction][lane][self.index-1].image.get_rect().width 
                - stoppingGap         
            elif(direction=='left'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                + vehicles[direction][lane][self.index-1].image.get_rect().width 
                + stoppingGap
            elif(direction=='down'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                - vehicles[direction][lane][self.index-1].image.get_rect().height 
                - stoppingGap
            elif(direction=='up'):
                self.stop = vehicles[direction][lane][self.index-1].stop 
                + vehicles[direction][lane][self.index-1].image.get_rect().height 
                + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting and stopping coordinate
        if(direction=='right'):
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1 or self.lane==2):
                    if(self.crossed==0 or self.x+self.image.get_rect().width<stopLines[self.direction]+40):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1)
                                and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            if self.lane==1 :
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x += 2.4
                                self.y -= 2.8
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                self.x+=self.speed
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):
                                self.y -= self.speed

            else: 
                if(self.crossed == 0):
                    if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap))):                
                        self.x += self.speed
                else:
                    if((self.crossedIndex==0) or (self.x+self.image.get_rect().width<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):                 
                        self.x += self.speed
            if (signals[0].yellow==4 and signals[0].green==0
                and self.x + self.image.get_rect().width > self.stop
                and self.x + self.image.get_rect().width <= self.stop+50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the right direction  "
                                            f"Y = {self.x + self.image.get_rect().width} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x += self.speed
        elif(self.direction=='down'):
            if (self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if (self.willTurn == 0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1 or self.lane==2):
                    if(self.crossed==0 or self.y+self.image.get_rect().height<stopLines[self.direction]+50):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y += self.speed
                    else:
                        if(self.turned==0):
                            if self.lane==1 :
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x += 1.2
                                self.y += 1.8
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                self.y+=self.speed
                        else:
                            if(self.crossedIndex==0 or ((self.x + self.image.get_rect().width) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):
                                self.x += self.speed
            else:
                if(self.crossed == 0):
                    if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap))):
                        self.y += self.speed
                else:
                    if((self.crossedIndex==0) or (self.y+self.image.get_rect().height<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):
                        self.y += self.speed
            if (signals[1].yellow==4 and signals[1].green==0
                and self.y + self.image.get_rect().height > self.stop
                and self.y + self.image.get_rect().height <= self.stop+50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the down direction  "
                                            f"Y = {self.y + self.image.get_rect().height} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x += self.speed
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1 or self.lane==2):
                    if(self.crossed==0 or self.x>stopLines[self.direction]-70):
                        if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else: 
                        if(self.turned==0):
                            if self.lane==1 :
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x -= 1
                                self.y += 1.2
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else :
                                self.x-=self.speed
                        else:
                            if(self.crossedIndex==0 or ((self.y + self.image.get_rect().height) <(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y  -  movingGap))):
                                self.y += self.speed

            else: 
                if(self.crossed == 0):
                    if((self.x>=self.stop or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.x>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
            if (signals[2].yellow==4 and signals[2].green==0
                and self.x + self.image.get_rect().width > self.stop
                and self.x + self.image.get_rect().width <= self.stop+50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the left direction  "
                                            f"Y = {self.x + self.image.get_rect().width} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x += self.speed
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1):
                    if(self.crossed==0 or self.y>stopLines[self.direction]-60):
                        if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            if self.lane==1 :
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x -= 2
                                self.y -= 1.2
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):
                                    self.x -= self.speed
                        else :
                            self.x-=self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y>=self.stop or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.y>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed
            if (signals[3].yellow == 4 and signals[3].green == 0
                    and self.y + self.image.get_rect().height > self.stop
                    and self.y + self.image.get_rect().height <= self.stop + 50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the up direction  "
                                            f"Y = {self.y + self.image.get_rect().height} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x += self.speed

# Initialization of signals with default values
def initialize():
    minTime = randomGreenSignalTimerRange[0]
    maxTime = randomGreenSignalTimerRange[1]
    if(randomGreenSignalTimer):
        ts1 = TrafficSignal(0, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts1)
        ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts2)
        ts3 = TrafficSignal(defaultRed, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts3)
        ts4 = TrafficSignal(defaultRed, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts4)
    else:
        ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
        signals.append(ts1)
        ts2 = TrafficSignal(ts1.yellow+ts1.green, defaultYellow, defaultGreen[1])
        signals.append(ts2)
        ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
        signals.append(ts3)
        ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
        signals.append(ts4)
    repeat()

# Print the signal timers on cmd
def printStatus():
    for i in range(0, 4):
        if(signals[i] != None):
            if(i==currentGreen):
                if(currentYellow==0):
                    print(" GREEN TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
                else:
                    print("YELLOW TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
            else:
                print("   RED TS",i+1,"-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
    print()  

def repeat():
    global currentGreen, currentYellow, nextGreen
    while(signals[currentGreen].green>0):   # while the timer of current green signal is not zero
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 1   # set yellow signal on
    # reset stop coordinates of lanes and vehicles 
    for i in range(0,3):
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while(signals[currentGreen].yellow>0):  # while the timer of current yellow signal is not zero
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0   # set yellow signal off
    
    # reset all signal times of current signal to default/random times
    if(randomGreenSignalTimer):
        signals[currentGreen].green = random.randint(randomGreenSignalTimerRange[0],randomGreenSignalTimerRange[1])
    else:
        signals[currentGreen].green = defaultGreen[currentGreen]
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
       
    currentGreen = nextGreen # set next signal as green signal
    nextGreen = (currentGreen+1)%noOfSignals    # set next green signal
    signals[nextGreen].red = signals[currentGreen].yellow+signals[currentGreen].green    # set the red time of next to next signal as (yellow time + green time) of next signal
    repeat()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

# Generating vehicles in the simulation
def generateVehicles():
    while(True):
        vehicle_type = random.choice(allowedVehicleTypesList)
        lane_number = random.randint(1,2)
        will_turn = 0
        if(lane_number == 1):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        elif(lane_number == 2):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        temp = random.randint(0,99)
        direction_number = 0
        dist = [25,50,75,100]
        if(temp<dist[0]):
            direction_number = 0
        elif(temp<dist[1]):
            direction_number = 1
        elif(temp<dist[2]):
            direction_number = 2
        elif(temp<dist[3]):
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(2)

def showStats():
    totalVehicles = 0
    print('Direction-wise Vehicle Counts')
    for i in range(0,4):
        if(signals[i]!=None):
            print('Direction',i+1,':',vehicles[directionNumbers[i]]['crossed'])
            totalVehicles += vehicles[directionNumbers[i]]['crossed']
    print('Total vehicles passed:',totalVehicles)
    print('Total time:',timeElapsed)

def simTime():
    global timeElapsed, simulationTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simulationTime):
            showStats()
            os._exit(1)


####################################
##################################################
#########################################################
#####################################################################


# Default values of signal timers
defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
defaultRed = 150
defaultYellow = 5

noOfSignals = 4
currentGreen = 0  # Indicates which signal is green currently
nextGreen = (currentGreen + 1) % noOfSignals  # Indicates which signal will turn green next
currentYellow = 0  # Indicates whether yellow signal is on or off

speeds222 = { 'pedestrian': 0.5}  # average speeds of vehicles

# Coordinates of vehicles' start      "moving"
x222 = {'right': [0, 0, 0], 'down': [610, 590, 677], 'left': [1500, 1500, 1500], 'up': [647, 770, 702]}
y222 = {'right': [178, 505, 428], 'down': [0, 0, 0], 'left': [430, 320, 498], 'up': [987, 987, 987]}

vehicles222 = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes222 = {0: 'pedestrian', 1: 'pedestrian', 2: 'pedestrian', 3: 'pedestrian'}
directionNumbers222 = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}


# Coordinates of stop lines
stopLines222 = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop222 = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
# stops = {'right': [580,580,580], 'down': [320,320,320], 'left': [810,810,810], 'up': [545,545,545]}

# Gap between vehicles
stoppingGap222 = 15  # stopping gap
movingGap222 = 15  # moving gap
pygame.init()
simulation = pygame.sprite.Group()


class Vehicle222(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds222[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x222[direction][lane]
        self.y = y222[direction][lane]
        self.crossed = 0
        vehicles222[direction][lane].append(self)
        self.index = len(vehicles222[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        if (len(vehicles222[direction][lane]) > 1 and vehicles222[direction][lane][
            self.index - 1].crossed == 0):  # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
            if (direction == 'right'):
                self.stop = vehicles222[direction][lane][self.index - 1].stop - vehicles222[direction][lane][
                    self.index - 1].image.get_rect().width - stoppingGap222  # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap
            elif (direction == 'left'):
                self.stop = vehicles222[direction][lane][self.index - 1].stop + vehicles222[direction][lane][
                    self.index - 1].image.get_rect().width + stoppingGap222
            elif (direction == 'down'):
                self.stop = vehicles222[direction][lane][self.index - 1].stop - vehicles222[direction][lane][
                    self.index - 1].image.get_rect().height - stoppingGap222
            elif (direction == 'up'):
                self.stop = vehicles222[direction][lane][self.index - 1].stop + vehicles222[direction][lane][
                    self.index - 1].image.get_rect().height + stoppingGap222
        else:
            self.stop = defaultStop222[direction]

        # Set new starting and stopping coordinate
        if (direction == 'right'):
            temp = self.image.get_rect().width + stoppingGap222
            x222[direction][lane] -= temp
        elif (direction == 'left'):
            temp = self.image.get_rect().width + stoppingGap222
            x222[direction][lane] += temp
        elif (direction == 'down'):
            temp = self.image.get_rect().height + stoppingGap222
            y222[direction][lane] -= temp
        elif (direction == 'up'):
            temp = self.image.get_rect().height + stoppingGap222
            y222[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if (self.direction == 'right'):
            if (self.crossed == 0 and self.x + self.image.get_rect().width > stopLines222[
                self.direction]):  # if the image has crossed stop line now
                self.crossed = 1
            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    currentGreen == 0 and currentYellow == 0)) and (
                    self.index == 0 or self.x + self.image.get_rect().width < (
                    vehicles222[self.direction][self.lane][self.index - 1].x - movingGap222))):
                # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                self.x += self.speed  # move the vehicle
            if (signals[0].yellow==4 and signals[0].green==0
                and self.x + self.image.get_rect().width > self.stop
                and self.x + self.image.get_rect().width <= self.stop+50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the right direction  "
                                            f"X = {self.x + self.image.get_rect().width} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x += self.speed
        elif (self.direction == 'down'):
            if (self.crossed == 0 and self.y + self.image.get_rect().height > stopLines222[self.direction]):
                self.crossed = 1
            if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or (
                    currentGreen == 1 and currentYellow == 0)) and (
                    self.index == 0 or self.y + self.image.get_rect().height < (
                    vehicles222[self.direction][self.lane][self.index - 1].y - movingGap222))):
                self.y += self.speed
            if (signals[1].yellow==4 and signals[1].green==0
                and self.y + self.image.get_rect().height > self.stop
                and self.y + self.image.get_rect().height <= self.stop+50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the down direction  "
                                            f"Y = {self.y + self.image.get_rect().height} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop+50} ")
                self.crossed = 1
                self.x += self.speed
        elif (self.direction == 'left'):
            if (self.crossed == 0 and self.x < stopLines222[self.direction]):
                self.crossed = 1
            if ((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0)) and (
                    self.index == 0 or self.x > (
                    vehicles222[self.direction][self.lane][self.index - 1].x + vehicles222[self.direction][self.lane][
                self.index - 1].image.get_rect().width + movingGap222))):
                self.x -= self.speed
            if (signals[2].yellow==4 and signals[2].green==0
                and self.x + self.image.get_rect().width > self.stop
                and self.x + self.image.get_rect().width <= self.stop+50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the left direction  "
                                            f"X = {self.x + self.image.get_rect().width} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x -= self.speed
        elif (self.direction == 'up'):
            if (self.crossed == 0 and self.y < stopLines222[self.direction]):
                self.crossed = 1
            if ((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0)) and (
                    self.index == 0 or self.y > (
                    vehicles222[self.direction][self.lane][self.index - 1].y + vehicles222[self.direction][self.lane][
                self.index - 1].image.get_rect().height + movingGap222))):
                self.y -= self.speed
            if (signals[3].yellow == 4 and signals[3].green == 0
                    and self.y + self.image.get_rect().height > self.stop
                    and self.y + self.image.get_rect().height <= self.stop + 50):
                messagebox.showinfo("note", f"there is a violation {self.vehicleClass}  from the up direction  "
                                            f"Y = {self.y + self.image.get_rect().height} and  stop point ={self.stop}"
                                            f"and  rang of violation is {self.stop + 50} ")
                self.crossed = 1
                self.x += self.speed



# Generating vehicles in the simulation
def generateVehicles222():
    while (True):
        vehicle_type = random.randint(0, 3)
        lane_number = random.randint(1, 1)
        temp = random.randint(0, 99)
        direction_number = 0
        dist = [25, 50, 75, 100]
        if (temp < dist[0]):
            direction_number = 0
        elif (temp < dist[1]):
            direction_number = 1
        elif (temp < dist[2]):
            direction_number = 2
        elif (temp < dist[3]):
            direction_number = 3
        Vehicle222(lane_number, vehicleTypes222[vehicle_type], direction_number, directionNumbers222[direction_number])
        time.sleep(5)


class Main:
    global allowedVehicleTypesList

    i = 0
    for vehicleType in allowedVehicleTypes:
        if(allowedVehicleTypes[vehicleType]):
            allowedVehicleTypesList.append(i)
        i += 1
    thread1 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread1.daemon = True
    thread1.start()

    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    # Loading  pedestrians signals
    pedestriansgreenSignal = pygame.image.load('images\pedestrians signals/green.png')
    pedestriansredSignal = pygame.image.load('images\pedestrians signals/red.png')

    # Loading  pedestrians signals
    pedestriansgreenSignalH = pygame.image.load('images\pedestrians signals\horizantol/green.png')
    pedestriansredSignalH = pygame.image.load('images\pedestrians signals\horizantol/red.png')

    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')



    font = pygame.font.Font(None, 30)
    thread2 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread2.daemon = True
    thread2.start()

    thread21 = threading.Thread(name="generateVehicles222", target=generateVehicles222, args=())  # Generating vehicles
    thread21.daemon = True
    thread21.start()

    thread3 = threading.Thread(name="simTime",target=simTime, args=())
    thread3.daemon = True
    thread3.start()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                showStats()
                sys.exit()

        screen.blit(background,(0,0))   # display background in simulation
        for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
            if(i==currentGreen):
                if(currentYellow==1):
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])

            else:
                if(signals[i].red<=10):
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]



        # display signal pedestrian
        screen.blit(pedestriansredSignalH, pd.signalCoodsHorizontal[0])
        screen.blit(pedestriansredSignal, pd.signalCoods[1])
        screen.blit(pedestriansredSignalH, pd.signalCoodsHorizontal[2])
        screen.blit(pedestriansredSignal, pd.signalCoods[3])

        for i in range(0,noOfSignals):
            if  signals[i].red==0 and signals[i].yellow==5 :
               # messagebox.showinfo("note",str(signals[i]))
                if i==0 or i==2 :
                    screen.blit(pedestriansgreenSignalH, pd.signalCoodsHorizontal[i -2])
                else:
                    screen.blit(pedestriansgreenSignal, pd.signalCoods[i-2])

        # display signal timer
        for i in range(0,noOfSignals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i])


        # display vehicle count
        for i in range(0,noOfSignals):
            displayText = vehicles[directionNumbers[i]]['crossed']
            vehicleCountTexts[i] = font.render(str(displayText), True, black, white)


        # display time elapsed

        # display the vehicles

        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()




        pygame.display.update()



Main()