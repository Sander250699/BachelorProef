# tutorial 10 gevolgd van de github om traffic lights te creeren!
# Wat doet deze code?
#   => one by one kruispunt creeeren
#   => 4 autos spawnen maar, kan de simulatie niet starten
# fout melding:
# "ValueError: 'a' cannot be empty unless no samples are taken"
# Kan dit opgelost worden met de inflow te regelenen?
import os
import pandas as pd
from flow.core.experiment import Experiment
from flow.core.params import NetParams
from flow.core.params import VehicleParams
from flow.core.params import InitialConfig
from flow.core.params import TrafficLightParams
from flow.core.params import SumoParams
from flow.core.params import EnvParams
from flow.core.params import SumoCarFollowingParams
from flow.networks import TrafficLightGridNetwork
from flow.envs import WaveAttenuationEnv
from flow.envs.traffic_light_grid import ADDITIONAL_ENV_PARAMS
from flow.envs.ring.accel import AccelEnv
from flow.controllers import SimCarFollowingController, GridRouter


print(ADDITIONAL_ENV_PARAMS)
horizon = 400
inner_length = 300
long_length = 100
short_length = 300
n = 1 # rows
m = 1 # columns
num_cars_left = 1
num_cars_right = 1
num_cars_top = 1
num_cars_bot = 1
n_left, n_right, n_top, n_bottom = 1,1,1,1
enter_speed = 30

# nog nakijken
#env_params = EnvParams(additional_params=ADDITIONAL_ENV_PARAMS)

vehicles = VehicleParams()

# sumo config 
sim_params = SumoParams(sim_step=0.1, render=True, emission_path='data')

#initial confic 
initial_config = InitialConfig(spacing="uniform", perturbation=1)

# voertuigen
vehicles.add("human",
    acceleration_controller=(SimCarFollowingController, {}),
    car_following_params=SumoCarFollowingParams(
        min_gap=2.5,
        max_speed=enter_speed,
        speed_mode="right_of_way",
    ), 
    routing_controller=(GridRouter, {}),
    num_vehicles=(n_left + n_right)*m + (n_top + n_bottom)*n
    )

grid_array = {"short_length": short_length, "inner_length": inner_length,
              "long_length": long_length, "row_num": n, "col_num": m,
              "cars_left": num_cars_left, "cars_right": num_cars_right,
              "cars_top": num_cars_top, "cars_bot": num_cars_bot}

# Verkeerlichten instellingen       # => zie tutorial 10
tl_logic=TrafficLightParams()
node = "center0"                                    
phasess = [{"duration": "31", "state": "GrGr"},
          {"duration": "6", "state": "yryr"},
          {"duration": "31", "state": "rGrG"},
          {"duration": "6", "state": "ryry"}]
    # toevoegen van de tl logic
tl_logic.add(node, tls_type="static", programID="1", offset=None, phases=phasess)

# toevoegen van de additional parameters 
additional_net_params = {"grid_array": grid_array, "speed_limit": 35,
                         "horizontal_lanes": 1, "vertical_lanes": 1,
                         "traffic_lights": True}
net_params=NetParams(additional_params=additional_net_params)

# creeren van het network (tutorial 10)
network = TrafficLightGridNetwork(name="grid",
                            vehicles=vehicles,
                            net_params=net_params,
                            initial_config=initial_config,
                            traffic_lights=tl_logic)

flow_params = dict(
    exp_tag='one by one',
    env_name="test",    # object aanmaken van de env                # hier moet de Env instance staan, wat bedoelt men hier juist mee?
    network=network,    # Moet dit erbij? want de env meegeven bij het env_name object                        # moet dit trafficLigtGridNetwork zijn of het gecreerde network object(lijn 84)
    simulator='traci',
    sim=sim_params,
    env=EnvParams(
        horizon=horizon,
        additional_params={
            "target_velocity": 30,
            "switch_time": 2,
            "num_observed": 2,
            "discrete": True,
            "tl_type": "static"
        }
    ),
    net=net_params,
    veh=vehicles,
    initial=initial_config,
    tls=tl_logic,
)

                
# number of time steps
flow_params['env'].horizon = 3000
exp = Experiment(flow_params)

# run the sumo simulation
_ = exp.run(1, convert_to_csv=True)
print("Alles oke")