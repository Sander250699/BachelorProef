import gym
import os
import sys
import optparse
import numpy as np

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

'''
matrix maken => op elke plek een tuple bestaande uit 
(reward, state) => state is tuple op zich
             => hoe observatie doen per kruispunt 
[(reward, state kr lb), ]

'''
class CustomEnvGrid(gym.Env):
    currentPhase = []
    penalties = []
    maxSpeed = 20.0
    carsNS = []
    carsEw = []
    def __init__(self):
        super(CustomEnvGrid, self).__init__()
        options = get_options()
        sumoCmd = ['sumo-gui', "-c", "grid.sumocfg", "--tripinfo-output", "tripinfogrid.xml"]
        traci.start(sumoCmd)
        print("alles goed gezet")
        
        for i in range(0,8):
            self.currentPhase.append((0, "V"))
            self.penalties.append(0)

    
    def step(self):
        if traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            return True
        else:
            return False

    def change(self, i, action):
        trafficL = str(i)
        if self.currentPhase[0] != action[0]:
            if action[1] == "V":
                self.takeAction(trafficL, 1)
                startTime = traci.simulation.getTime()
                while traci.simulation.getTime() < (startTime + 5):
                    self.step()
                    self.observationNewCars()
                self.takeAction(trafficL, action[0])
                self.startTimePhase[i] = traci.simulation.getTime()
                self.penalty[i] = 0.3
            else:
                self.takeAction(trafficL, 3)
                startTime = traci.simulation.getTime()
                while traci.simulation.getTime() < (startTime + 5):
                    self.step()
                    self.observationNewCars()
                self.takeAction(trafficL, action[0])
                self.startTimePhase[i] = traci.simulation.getTime()
                self.penalty[i] = 0.3
        else:
            self.takeAction(trafficL, action[0])
            if self.penalty[i] > 0:
                self.penalty[i] = self.penalty[i] - 0.005
        self.currentPhase[i] = action

    def takeAction(self, trafficLA, actionA):
        traci.trafficlight.setPhase(trafficLA, actionA)

    def computeReward(self, i):
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
        for i in range(0,4):
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
        if self.currentPhase[i] == (0,"V"):
            rewardNS = -(1/qNS*(delayNS)) - self.penalties[i]    #penaltie dat men heeft als men van phase veranderd
            rewardEW = -(1/qEW*(delayEW))

        elif self.currentPhase[i] == (2, "H"):
            rewardNS = -(1/qNS*(delayNS))
            rewardEW = -(1/qEW*(delayEW)) - self.penalties[i]    #penaltie dat men heeft als men van phase veranderd
        #bepalen van de volgende state
        '''if (rewardNS <= 0.006):
            nextState = (0, "V")
            print("new state => V")
        elif (rewardEW <= 0.002):
            nextState = (2, "H")
            print("new state => H")
        else:
            nextState = self.currentPhase
        '''
        reward = max(rewardNS,rewardEW)
        if reward == rewardNS: 
            nextState = (0, "V")
        if reward == rewardEW:
            nextState = (2, "H")
        print("NS: " + str(rewardNS) + " EW: " + str(rewardEW))
        return (-reward ,nextState)

    def observationNewCars(self, i):
        if i == 0: 
            self.carsNS = traci.lane.getLastStepVehicleIDs("B4B3_0") + traci.lane.getLastStepVehicleIDs("B2B3_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("C3B3_0") + traci.lane.getLastStepVehicleIDs("A3B3_0")
        elif i == 1:
            self.carsNS = traci.lane.getLastStepVehicleIDs("C4C3_0") + traci.lane.getLastStepVehicleIDs("C2C3_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("D3C3_0") + traci.lane.getLastStepVehicleIDs("B3C3_0")
        elif i == 2:
            self.carsNS = traci.lane.getLastStepVehicleIDs("D4D3_0") + traci.lane.getLastStepVehicleIDs("D2D3_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("E3D3_0") + traci.lane.getLastStepVehicleIDs("C3D3_0")
        elif i == 3:
            self.carsNS = traci.lane.getLastStepVehicleIDs("B3B2_0") + traci.lane.getLastStepVehicleIDs("B1B2_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("C2B2_0") + traci.lane.getLastStepVehicleIDs("A2B2_0")
        elif i == 4:
            self.carsNS = traci.lane.getLastStepVehicleIDs("C3C2_0") + traci.lane.getLastStepVehicleIDs("C1C2_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("D2C2_0") + traci.lane.getLastStepVehicleIDs("B2C2_0")
        elif i == 5:
            self.carsNS = traci.lane.getLastStepVehicleIDs("D3D2_0") + traci.lane.getLastStepVehicleIDs("D1D2_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("E2D2_0") + traci.lane.getLastStepVehicleIDs("C2D2_0")
        elif i == 6:
            self.carsNS = traci.lane.getLastStepVehicleIDs("B2B1_0") + traci.lane.getLastStepVehicleIDs("B0B1_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("C1B1_0") + traci.lane.getLastStepVehicleIDs("A1B1_0")
        elif i == 7:
            self.carsNS = traci.lane.getLastStepVehicleIDs("C2C1_0") + traci.lane.getLastStepVehicleIDs("C0C1_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("D1C1_0") + traci.lane.getLastStepVehicleIDs("B1C1_0")
        elif i == 8:
            self.carsNS = traci.lane.getLastStepVehicleIDs("D2D1_0") + traci.lane.getLastStepVehicleIDs("D0D1_0")
            self.carsEW = traci.lane.getLastStepVehicleIDs("E1D1_0") + traci.lane.getLastStepVehicleIDs("C1D1_0")
        self.printCars(i)

    def printCars(self, i):
        print(str(i) + " NS: " + str(self.carsNS))
        print(str(i) + " EW: " + str(self.carsEW)) 

    def reset(self):
        self.carsNS = []
        self.carsEW = []
        print("alles gereset")
    
    def reward(self):
        print("reward berekend")