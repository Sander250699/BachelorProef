# uitvoering van de tutorial over de inflow en uitflow van open networks 
from flow.networks import MergeNetwork
from flow.core.params import VehicleParams
from flow.core.params import SumoCarFollowingParams
from flow.controllers import IDMController
from flow.networks.merge import ADDITIONAL_NET_PARAMS
from flow.core.params import NetParams
from flow.core.params import SumoParams, EnvParams, InitialConfig
from flow.envs.ring.accel import AccelEnv, ADDITIONAL_ENV_PARAMS
from flow.core.experiment import Experiment
# Nodig voor de inflow te maken
from flow.core.params import InFlows
# create a vehicle type
vehicles = VehicleParams()
vehicles.add("human",
             acceleration_controller=(IDMController, {}),
             car_following_params=SumoCarFollowingParams(
                 speed_mode="obey_safe_speed"))


# create the inflows
inflows = InFlows()

# inflow for (1)
inflows.add(veh_type="human",
            edge="inflow_highway",
            vehs_per_hour=10000,
            depart_lane="random",
            depart_speed="random",
            color="red")

# inflow for (2)
inflows.add(veh_type="human",
            edge="inflow_merge",
            period=2,
            depart_lane=0,  # right lane
            depart_speed=0,
            color="red")

# inflow for (3)
inflows.add(veh_type="human",
           edge="inflow_merge",
           probability=0.1,
           depart_lane=1,  # left lane
           depart_speed="max",
           begin=60,  # 1 minute
           number=30,
           color="red")


# modify the network accordingly to instructions
# (the available parameters can be found in flow/networks/merge.py)
additional_net_params = ADDITIONAL_NET_PARAMS.copy()
additional_net_params['post_merge_length'] = 350  # this is just for visuals
additional_net_params['highway_lanes'] = 4
additional_net_params['merge_lanes'] = 2


# setup and run the simulation
net_params = NetParams(inflows=inflows,
                       additional_params=additional_net_params)

sim_params = SumoParams(render=True,
                         sim_step=0.2)
sim_params.color_vehicles = False
print(ADDITIONAL_ENV_PARAMS)
env_params = EnvParams(additional_params=ADDITIONAL_ENV_PARAMS)

initial_config = InitialConfig()

flow_params = dict(
    exp_tag='merge-example',
    env_name=AccelEnv,
    network=MergeNetwork,
    simulator='traci',
    sim=sim_params,
    env=env_params,
    net=net_params,
    veh=vehicles,
    initial=initial_config,
)

# number of time steps
flow_params['env'].horizon = 10000
exp = Experiment(flow_params)

# run the sumo simulation
_ = exp.run(1)