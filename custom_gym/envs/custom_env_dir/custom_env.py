import gym
from gym import spaces
import os
import sys
import optparse

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment")

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options

import traci


class CustomEnv(gym.Env):
    carsNS = []
    carsEW = []
    penalty= 0
    maxSpeed = 19.44
    def __init__(self):
        print('Env initialised')

        # sumo installeren 
        options = get_options()
        sumoCmd = ['sumo-gui', "-c", "baptest2.sumocfg", "--tripinfo-output", "tripinfo.xml"]
        traci.start(sumoCmd)
        
        # action - en observation state 
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Discrete(2)
        self.currentPhase = (0, "V")

    def change(self, action):
        if self.currentPhase[0] != action[0]:
            print("huidige fase:" + str(self.currentPhase) + " volgende fase: " + str(action))
            if action[1] == "V":
                self.takeAction(1)
                startTime = traci.simulation.getTime()
                while traci.simulation.getTime() < (startTime + 5):
                    self.step()
                self.takeAction(action[0])
                self.penalty = 0.5
            else:
                self.takeAction(3)
                startTime = traci.simulation.getTime()
                while traci.simulation.getTime() < (startTime + 5):
                    self.step()
                self.takeAction(action[0])
                self.penalty = 0.5
        else:
            if self.penalty > 0:
                self.penalty = self.penalty - 0.05
        self.currentPhase = action
    
    def step(self):
        if traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            return True
        else:
            return False
    
    def printCars(self):
        print(self.carsNS)
        print(self.carsEW)

    def observation(self):
        self.carsNS = traci.lane.getLastStepVehicleIDs("4i_0") + traci.lane.getLastStepVehicleIDs("3i_0")
        self.carsEW = traci.lane.getLastStepVehicleIDs("2i_0") + traci.lane.getLastStepVehicleIDs("1i_0")


    
    def computeReward(self):
        # max snelheid van de verschillende lanen
        lN = traci.lane.getMaxSpeed("4i_0")
        lE = traci.lane.getMaxSpeed("2i_0")
        lS = traci.lane.getMaxSpeed("3i_0")
        lW = traci.lane.getMaxSpeed("1i_0")
        
        # aantal wachtende auto's per richting
        qNS = len(self.carsNS)
        qEW = len(self.carsEW)
        print("NS: " + str(qNS) + " EW: " + str(qEW))
        if qNS == 0:
            qNS = 1
        if qEW == 0:
            qEW = 1
        #delay 
        delayNS = 0.0
        delayEW = 0.0
        for i in range(0,3):
            if i < len(self.carsNS):
                carNS = self.carsNS[i]
                delayNS = delayNS + (self.maxSpeed - traci.vehicle.getSpeed(carNS))
            if i < len(self.carsEW):
                carEW = self.carsEW[i]
                delayEW = delayEW + (self.maxSpeed - traci.vehicle.getSpeed(carEW))
        if delayNS <= 0:
            delayNS = 1
        if delayEW <= 0:
            delayEW = 1

        # berekening van de reward
        if self.currentPhase == (0, "V"):
            rewardNS = -(1/qNS*(delayNS) + self.penalty)  #penaltie dat men heeft als men van phase veranderd
            rewardEW = -(1/qEW*(delayEW))
        elif self.currentPhase == (2, "H"):
            rewardNS = -(1/qNS*(delayNS))
            rewardEW = -(1/qEW*(delayEW) + self.penalty)  #penaltie dat men heeft als men van phase veranderd            
        #bepalen van de volgende state
        '''if (rewardNS <= 0.3):
            nextState = (0, "V")
            print("new state => V")
        elif (rewardEW <= 0.3):
            nextState = (2, "H")
            print("new state => H")
        else:
            nextState = self.currentPhase'''
        reward = max(rewardNS,rewardEW)
        if reward == rewardNS: 
            nextState = (0, "V")
        if reward == rewardEW:
            nextState = (2, "H")
        print("NS: " + str(rewardNS) + " EW: " + str(rewardEW))
        return (-reward ,nextState)
    
    def takeAction(self, action):
        traci.trafficlight.setPhase("0", action)
    
    def reset(self):
        self.carsNS = []
        self.carsEW = []
        print("reset gebeurd")
    
    def getReward(self):
        print('reward ontvangen')
