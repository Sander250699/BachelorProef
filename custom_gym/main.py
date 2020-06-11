import gym
from gym import spaces
from ray import rllib
import envs
import ray
import gym
import os
import sys
import optparse
import numpy as np
import random
from ray.rllib.agents import ppo
# importeren van de agent 
from ray.rllib.agents.dqn import DQNTrainer
from ray.tune.logger import pretty_print



# state's
# 0 => verticaal heeft groen 
# 1 => horizontaal heeft groen

# Hyperparameters
ALPHA = 0.5
GAMMA = 0.1
epsilon = 0.1
# parameters voor omgeving

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

# one by one environment
class CustomEnv(rllib.env.MultiAgentEnv):
    carsNS = []
    carsEW = []
    penalty= 0
    maxSpeed = 19.44
    def __init__(self, env_config):
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
    
    def step(self, action):
        self.change(action)
        if traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            done = True
        else:
            done = False
        self.observation()
        endReward, stateNext = self.computeReward()
        obs = self.carsNS + self.carsEW
        print(obs)
        return obs, endReward, done

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
        obs = self.carsNS + self.carsEW
        return obs
    
    def getReward(self):
        print('reward ontvangen')





# determine the correct state, corresponding to the action
def determineActionToNumber(nextStateS):
    nextState = 0
    if nextStateS == (2,"H"):
        nextState = 1
    elif nextStateS == (0,"V"):
        nextState = 0
    return nextState

# determine the correct state, corresponding to the action
def determineState(action):
    actionS = (2, "H")
    if action == 1:
        actionS = (2, "H")
    elif action == 0:
        actionS = (0, "V")
    return actionS





if __name__ == "__main__":
    # error dat er niet genoeg geheugen vrij is, => met memory kan men dit aanpassen (parameter wordt niet herkent door ray)
    ray.init()                # => UITLEG BIJ VRAGEN
    trainer = ppo.PPOTrainer(config=None, env=CustomEnv, logger_creator=None)
    for i in range(0,2):
        print(trainer.train())

    
    
    
    '''currentState = 1                     # (2, "H")
    nextStateS = (2 ,"H")
    nextState = 1
    action = 1 
    actionS = (2, "H")   
    # config van de agent       => UITLEG BIJ VRAGEN
    trainer = DQNTrainer(env="CustomEnv-v0", config={"eager": True})
    model = trainer.get_policy().model
    # Opzetten van de environment voor onebyone
    config = {}
    env = CustomEnv(config)
    # env = gym.make('CustEnv-v0')
    env.reset()     
    # Initialiseren van de q_table_obo
   
    busy = True
    while busy:
        busy = env.step()
    env.reset()
    '''
    print("dit is bap map")
    
    
    
    
    
    '''
    # Todo nog q - learning alg implementeren voor grid
    # Opzetten van de environment voor grid
    env1 = gym.make('CustEnvGrid-v0')
    # Initialisatie van de variabelen
    actionSpace = 2
    observationSpace = 9
    M = np.zeros((actionSpace, observationSpace))
    res =  np.array(list(zip(M.ravel(),M.ravel())), dtype=('i4,i4')).reshape(M.shape)
    #print(res)
    busyGrid = True
    while busyGrid:
        # choose action aan de hand van de greedy policy => met epsilon
        #nextPhase = (...,...)
        # take the action and observe reward and next state + step uitvoeren 
        #env1.change(nextState)
        busyGrid = env1.step()
        # observatie doen
        for i in range (0,9):
            env1.observationNewCars(i)
        # reward bepalen 
            reward, nextState = env1.computeReward(i)
            print(str(i) + " Reward: " + str(reward))
        # transition storen
        # reset maken van alle listen
            env1.reset()
    print('env aangemaakt')
    env1.reset()
    print("dit is bap map")
    # einde '''