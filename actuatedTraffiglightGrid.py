from flow.networks.traffic_light_grid import TrafficLightGridNetwork
from flow.core.params import SumoParams, EnvParams, NetParams, InitialConfig, InFlows, SumoCarFollowingParams, VehicleParams, \
    InFlows, NetParams, TrafficLightParams
from flow.controllers import SimCarFollowingController, GridRouter
from flow.envs import TrafficLightGridPOEnv
from flow.core.experiment import Experiment


def getOmgeving():
    sim_params = SumoParams(render=True, sim_step=1,restart_instance=True)
    '''
    Opstelling van het netwerk:
        |   |   |
    -6---7---8--
    -3---4---5--
    -0---1---2--
        |   |   | 
    '''

    # bij deze code is er het probleem dat de de routes niet gekend zijn in de simulatie, de voertuigen kunnen gen gedefinieerde route volgen
    # params for grid env
    HORIZON = 400               # Time horizon of a single rollout
    inner_length = 300
    long_length = 500
    short_lengh = 500
    rows = 3
    columns = 3
    num_cars_left = 1
    num_cars_right = 1
    num_cars_top = 1
    num_cars_bottom = 1
    enterSpeed = 30 
    tot_cars = (num_cars_left + num_cars_right)*columns + (num_cars_top + num_cars_bottom)*rows
    grid_array = {
        "short_length": short_lengh, 
        "inner_length": inner_length, 
        "long_length": long_length, 
        "row_num": rows, 
        "col_num": columns,
        "cars_left": num_cars_left, 
        "cars_right": num_cars_right, 
        "cars_top": num_cars_top, 
        "cars_bot": num_cars_bottom
        }
    # vehicles
    vehicles = VehicleParams()
    vehicles.add(
        "human",
        acceleration_controller=(SimCarFollowingController, {}),
        car_following_params=SumoCarFollowingParams(
            speed_mode="right_of_way",
            min_gap=2.5,
            max_speed=enterSpeed,
            decel=7.5,   
        ),
        routing_controller=(GridRouter, {}),
        num_vehicles=tot_cars)

    # inflow 
    # outer_edges of the network (zie traffic_light_grid.py file)
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
            #vehs_er_hour=edge_inflow
            depart_lane="free",
            depart_speed=enterSpeed)
    # net params 
    additional_net_params = {
        "grid_array": grid_array, 
        "speed_limit": 50,
        "horizontal_lanes": 1, 
        "vertical_lanes": 1}
        #"traffic_lights": True}
    net_params = NetParams(inflows=inflow, additional_params=additional_net_params)

    # env params
    additional_env_params = {
        "switch_time": 3.0, 
        "tl_type": "controlled", 
        "discrete": True, 
        "num_observed":2,
        "target_velocity": 50
        }
    env_params = EnvParams(horizon=HORIZON, additional_params=additional_env_params)
    # initial config
    initial_config = InitialConfig(spacing="custom", shuffle=True)

    # flow params
    flow_param = dict(
        # name of the experiment
        exp_tag="RL_traffic_lights_grid",
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
    return flow_param

if __name__ == "__main__":
    flow_params = getOmgeving()
    # runnen van de simulatie 1 
    print("run 1")
    flow_params['env'].horizon = 3000
    exp = Experiment(flow_params)
        #run the simulation
    _ = exp.run(1, convert_to_csv=False)
    print("run 2")
    flow_params['env'].horizon = 3000
    exp = Experiment(flow_params)
        #run the simulation
    _ = exp.run(1, convert_to_csv=False)