
from flow.networks.traffic_light_grid import TrafficLightGridNetwork
from flow.core.params import SumoParams, EnvParams, NetParams, InitialConfig, InFlows, SumoCarFollowingParams, VehicleParams, \
    InFlows, NetParams, TrafficLightParams
from flow.controllers import SimCarFollowingController, GridRouter
from flow.envs import TrafficLightGridEnv
from flow.core.experiment import Experiment
sim_params = SumoParams(render=True, sim_step=0.2, restart_instance=False)
# params for grid env
inner_length = 300
long_length = 500
short_lengh = 500
rows = 1
columns = 1
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
# bij deze code is er het probleem dat de de routes niet gekend zijn in de simulatie, de voertuigen kunnen gen gedefinieerde route volgen
# dit valt misschien op te lossen door de routes in de code zelf te definieren en ze mee te geven met de net params, kunnen die daar echter gedefinieerd 
# mee worden? 


# vehicles
    # add the starting vehicles 
vehicles = VehicleParams()
vehicles.add("human",
             acceleration_controller=(SimCarFollowingController, {}),
             car_following_params=SumoCarFollowingParams(
                 speed_mode="right_of_way",
                 min_gap=2.5  
             ),
             routing_controller=(GridRouter, {}),
             num_vehicles=tot_cars)

# inflow
    # outer_edges of the network (zie traffic_light_grid.py file)
outer_edges = []
outer_edges += ["left{}_{}".format(rows, i) for i in range(columns)]
outer_edges += ["right0_{}".format(i) for i in range(rows)]
outer_edges += ["bot{}_0".format(i) for i in range(columns)]
outer_edges += ["top{}_{}".format(i, columns) for i in range(rows)]
inflow = InFlows()
for edge in outer_edges:
    if edge=="left1_0":
        prob=0.10
    elif edge=="right0_0":
        prob=0.10
    elif edge=="bot0_0":
        prob=0.10
    elif edge=="top0_1":
        prob=0.10
    inflow.add(
        veh_type="human",
        edge=edge,
        #probability=prob,
        vehs_per_hour=2000,
        depart_lane=0,
        depart_speed="max",
        )

# Net Params
additional_net_params = {
    "grid_array": grid_array, "speed_limit": 35,
    "horizontal_lanes": 1, "vertical_lanes": 1,
    "traffic_lights": True}
net_params = NetParams(inflows=inflow, additional_params=additional_net_params)

# Env Params
additional_env_params = {"switch_time": 3.0, "tl_type": "controlled", "discrete": True}
env_params = EnvParams(additional_params=additional_env_params)

# Initial config
# Wanneer je als spacing unifrom of random gebruikt dan kent het programma de routes niet, om dit op te lossen 
# moet er een custom spacing gebruikt worden
initial_config = InitialConfig(spacing='custom', shuffle=True)

# Flow Params
flow_params = dict(
    # name of the experiment
    exp_tag="onebyone",
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
    #number of time steps
flow_params['env'].horizon = 3000
exp = Experiment(flow_params)
    #run the simulation
_ = exp.run(1, convert_to_csv=False)
