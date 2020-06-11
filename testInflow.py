# Testen van de inflow  op een grid env
# network
from flow.networks import TrafficLightGridNetwork
# env 
from flow.envs import TrafficLightGridPOEnv
# parameters van netwerk en env
from flow.core.params import NetParams, EnvParams, SumoParams, InitialConfig, InFlows, VehicleParams
# Controllers 
from flow.controllers import GridRouter, SimCarFollowingController
#   A router used to re-route a vehicle in a traffic light grid environment.
#   MinicityRouter => A router used to continuously re-route vehicles in minicity network
#       Misschien kan dit ook gebruikt worden, al lijkt gridrouter beter in dit geval
# Parameters for sumo-controlled acceleration behavior
from flow.core.params import SumoCarFollowingParams
# experiment import 
from flow.core.experiment import Experiment

# time horizon of a single rollout
HORIZON = 400
# params voor het netwerk, zie https://github.com/flow-project/flow/blob/master/flow/networks/traffic_light_grid.py
rown = 1
collumn = 1
inner_length = 300
long_length = 500
short_lengh = 500
cars_t = 2
cars_b = 2
cars_l = 2
cars_r = 2
enter = 30
edge_inflow = 300
# Bepalen van de inflow, zie https://github.com/flow-project/flow/blob/master/tutorials/tutorial11_inflows.ipynb
inflow = InFlows()
# naam van de edges, waarop de voertuigen moeten spawnen
outer_edges = []
outer_edges += ["left{}_{}".format(rown, i) for i in range(collumn)]
outer_edges += ["right0_{}".format(i) for i in range (rown)]
outer_edges += ["bot{}_0".format(i) for i in range(rown)]
outer_edges += ["top{}_{}".format(i, collumn) for i in range(rown)]
# meerdere outeredges
# prob is de statistische kans dat er een voertuig gaat spawnen op die edge, dit valt te ver
# vangen met veh_per_our, waarbij dat aantal voertuigen per uur gaan spawnen. 
# op elke edge heeft men een inflow van 2000 voertuigen per uur.  
for edge in outer_edges:
    inflow.add(
        edge=edge,
        veh_type="human",
        depart_lane="free",              # van de grid1.py benchmark
        vehs_per_hour=edge_inflow,
        depart_speed=enter)

# ADDITIONAL NET PARAMS
# deze moeten geplaatst worden in een grid array
grid_array = {
    # number of horizontal rows of edges
    "row_num": rown,
    # number of vertical columns of edges
    "col_num": collumn,
    # length of inner edges in the traffic light grid network
    "inner_length": inner_length,
    # length of edges where vehicles enter the network
    "short_length": short_lengh,
    # length of edges where vehicles exit the network
    "long_length": long_length,
    # number of cars starting at the edges heading to the top
    "cars_top": cars_t,
    # number of cars starting at the edges heading to the bottom
    "cars_bot": cars_b,
    # number of cars starting at the edges heading to the left
    "cars_left": cars_l,
    # number of cars starting at the edges heading to the right
    "cars_right": cars_r
}
additional_net_params = {
    "speed_limit": 35,
    "grid_array": grid_array,
    # number of lanes in the horizontal edges, in 1 richting
    "horizontal_lanes": 1,
    # number of lanes in the vertical edges, in 1 richting
    "vertical_lanes": 1,
    # speed limit for all edges, may be represented as a float value, or a
    # dictionary with separate values for vertical and horizontal lanes
}
net_params = NetParams(inflows=inflow, additional_params=additional_net_params)

# ADDITIONAL ENV PARAMS
# params voor de omgeving, zie https://github.com/flow-project/flow/blob/master/flow/envs/traffic_light_grid.py
additional_env_params = {
    # minimum switch time for each traffic light (in seconds), de oranje fase
    "switch_time": 2.0,
    # whether the traffic lights should be actuated by sumo or RL
    # options are "controlled" and "actuated" => dus gecontroleerd bij sumo
    "tl_type": "controlled",
    # determines whether the action space is meant to be discrete or continuous
    "discrete": True,          # continous in dit geval
    # parameters voor PO
    "target_velocity": 50,
    "num_observed": 2
}
env_params = EnvParams(horizon=HORIZON,additional_params=additional_env_params)

# TOEVOEGEN VAN START VOERTUIGEN 
vehicles = VehicleParams()
vehicles.add(
    veh_id="human",
    acceleration_controller=(SimCarFollowingController, {}),
    car_following_params= SumoCarFollowingParams(
        speed_mode="right_of_way",
        min_gap=2.5,
        decel=7.5,
        max_speed=enter,
    ),
    routing_controller=(GridRouter, {}),
    num_vehicles=collumn*(cars_r + cars_l) + rown*(cars_t + cars_b))

# SIMULATION PARAMS
sim_params = SumoParams(render=True, sim_step=1, restart_instance=True)

# INITIAL CONFIG
# Wanneer je als spacing unifrom of random gebruikt dan kent het programma de routes niet, om dit op te lossen 
# moet er een custom spacing gebruikt worden
initial_config = InitialConfig(spacing='custom', shuffle=True)



# FLOW PARAMS
flow_params = dict(
    # name of the experiment
    exp_tag="onebyone",
    # name of the flow environment the experiment is running on
    env_name=TrafficLightGridPOEnv,
    # name of the network class the experiment uses
    network=TrafficLightGridNetwork,
    # simulator that is used by the experiment
    simulator='traci',
    # simulation-related parameters
    sim=sim_params,
    # environment related parameters (see flow.core.params.EnvParams)
    env=env_params,
    # network-related parameters (see flow.core.params.NetParams and
    # the network's documentation or ADDITIONAL_NET_PARAMS component)
    net=net_params,
    # vehicles to be placed in the network at the start of a rollout 
    # (see flow.core.vehicles.Vehicles)
    veh=vehicles,
    # (optional) parameters affecting the positioning of vehicles upon 
    # initialization/reset (see flow.core.params.InitialConfig)
    initial=initial_config
)


# runnen van de simulatie 
flow_params['env'].horizon = 3000
exp = Experiment(flow_params)
    #run the simulation
_ = exp.run(1, convert_to_csv=False)