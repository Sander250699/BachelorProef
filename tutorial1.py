import os
import pandas as pd
from flow.networks.ring import RingNetwork
from flow.envs.ring.accel import AccelEnv
from flow.core.params import VehicleParams
from flow.core.params import NetParams
from flow.core.params import InitialConfig #specifies parameters that affect the positioning of vehicle in the network at the start of a simulation
from flow.core.params import TrafficLightParams
from flow.core.params import SumoParams    # de parameters die we nog is hebben om sumo te runnen
from flow.core.params import EnvParams
from flow.core.experiment import Experiment #opzetten van het expirement
# ?
from flow.controllers.car_following_models import IDMController
# reroute all vehicles to the initial set route
from flow.controllers.routing_controllers import ContinuousRouter
# toevoegen van extra parameters
from flow.networks.ring import ADDITIONAL_NET_PARAMS
from flow.envs.ring.accel import ADDITIONAL_ENV_PARAMS
# naam van de simulatie 
name = "ring_example"

#creating empty vehicleParamsobject/ trafficlightobject
vehicles = VehicleParams()
trafficL = TrafficLightParams()
# simulation parameters 
sim_params = SumoParams(sim_step=0.1, render=True, emission_path='data')
# 22 voertuigen toevoegen met bovenstaande acceleration and routing behavior
vehicles.add("human",
            acceleration_controller=(IDMController, {}),
            routing_controller=(ContinuousRouter, {}),
            num_vehicles=22)
net_params = NetParams(additional_params=ADDITIONAL_NET_PARAMS)
env_params = EnvParams(additional_params=ADDITIONAL_ENV_PARAMS)
# initial config voor de simulatie, 

initial_config = InitialConfig(spacing="uniform", perturbation=1)
# vinden we de nodigeparameters mee terug
print(ADDITIONAL_NET_PARAMS)
print("runnen v/ h expirement")
flow_params = dict(
    exp_tag ='ring_example',
    env_name=AccelEnv,              
    network=RingNetwork,
    simulator='traci',
    sim=sim_params,
    env=env_params,
    net=net_params,
    veh=vehicles,
    initial=initial_config,
    tls=trafficL, 
)
#number of time steps
flow_params['env'].horizon = 3000
exp = Experiment(flow_params)
#run the simulation
_ = exp.run(1, convert_to_csv=True)
# info opver de simulatie 
emission_location = os.path.join(exp.env.sim_params.emission_path, exp.env.network.name)
print(emission_location + '-emission.xml')
# omzetten naar een csv file 
pd.read_csv(emission_location + '-emission.csv')
print("experiment is gerunned")

# toevoegen van vehicles doet men met behulp van vehicles.add() waarmee men hun gedrag kan specifieren
#if __name__ == "__main__":