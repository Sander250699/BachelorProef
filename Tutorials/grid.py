from flow.networks.traffic_light_grid import TrafficLightGridNetwork
from flow.core.params import SumoParams, EnvParams, NetParams, InitialConfig, InFlows, SumoCarFollowingParams, VehicleParams, \
    InFlows, NetParams, TrafficLightParams
from flow.controllers import SimCarFollowingController, GridRouter
from flow.envs import TrafficLightGridEnv
from flow.core.experiment import Experiment
sim_params = SumoParams(render=True, sim_step=0.2,restart_instance=True)
# bij deze code is er het probleem dat de de routes niet gekend zijn in de simulatie, de voertuigen kunnen gen gedefinieerde route volgen
# params for grid env
inner_length = 300
long_length = 500
short_lengh = 500
rows = 3
columns = 3
num_cars_left = 1
num_cars_right = 1
num_cars_top = 1
num_cars_bottom = 1
tot_cars = (num_cars_left + num_cars_right)*rows + (num_cars_top + num_cars_bottom)*columns
grid_array = {
    "short_length": short_lengh, "inner_length": inner_length, 
    "long_length": long_length, "row_num": rows, "col_num": columns,
    "cars_left": num_cars_left, "cars_right": num_cars_right, 
    "cars_top": num_cars_top, "cars_bot": num_cars_bottom
    }
# traffic lights
tl_logic = TrafficLightParams()
''' Opstelling gaat van volgende naart zijn 
    |   |   |
   -6---7---8--
   -3---4---5--
   -0---1---2--
    |   |   | 
'''
nodes = ["center0","center1","center2","center3","center4","center5","center6","center7","center8",]
phases = [{"duration": "31", "state": "GrGr"},
          {"duration": "6", "state": "yryr"},
          {"duration": "31", "state": "rGrG"},
          {"duration": "6", "state": "ryry"}]
for nodeid in nodes:
    tl_logic.add(
    nodeid,
    tls_type="static",
    programID=1,
    offset=None,
    phases=phases)
# vehicles
vehicles = VehicleParams()
vehicles.add(
    "human",
    acceleration_controller=(SimCarFollowingController, {}),
    car_following_params=SumoCarFollowingParams(
        speed_mode="right_of_way",
        min_gap=2.5  
    ),
    routing_controller=(GridRouter, {}),
    num_vehicles=tot_cars)
# inflow, probleem met de inflow is er nog steeds, geen routes gedefinieerd
inflow = InFlows()
outer_edges = []
outer_edges += ["left{}_{}".format(rows, i) for i in range(columns)]
outer_edges += ["right0_{}".format(i) for i in range (rows)]
outer_edges += ["bot{}_0".format(i) for i in range(rows)]
outer_edges += ["top{}_{}".format(i, columns) for i in range(rows)]
    # meerdere outeredges 
for edge in outer_edges:
    # collumns 
    if edge == "bot0_0":
        prob = 0.10
    if edge == "bot1_0":
        prob = 0.10
    if edge == "bot2_0":
        prob = 0.10 
    if edge == "top0_3":
        prob = 0.10
    if edge == "top1_3":
        prob = 0.10
    if edge == "top2_3":
        prob = 0.10
    # rows 
    if edge == "right0_0":
        prob = 0.10
    if edge == "right0_1":
        prob = 0.10
    if edge == "right0_2":
        prob = 0.10
    if edge == "left3_0":
        prob = 0.10
    if edge == "left3_1":
        prob = 0.10
    if edge == "left3_2":
        prob = 0.10
    # inflow 
    inflow.add(
        edge=edge,
        veh_type="human",
        probability=prob,
        depart_lane="first",
        depart_speed="max")
# net params 
additional_net_params = {
    "grid_array": grid_array, "speed_limit": 35,
    "horizontal_lanes": 1, "vertical_lanes": 1,
    "traffic_lights": True}
net_params = NetParams(additional_params=additional_net_params, inflows=inflow)
# env params
addition_env_parameters = {"switch_time": 3.0, "tl_type": "controlled", "discrete": True}
env_params = EnvParams(additional_params=addition_env_parameters)
# initial config
initial_config = InitialConfig(spacing="random", perturbation=1)
# flow params
flow_params = dict(
    # name of the experiment
    exp_tag="grid",
    # name of the flow environment the experiment is running on
    env_name=TrafficLightGridEnv,
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