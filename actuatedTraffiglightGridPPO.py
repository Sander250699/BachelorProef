# omgeving Parameters
from flow.networks.traffic_light_grid import TrafficLightGridNetwork
from flow.core.params import SumoParams, EnvParams, NetParams, InitialConfig, InFlows, SumoCarFollowingParams, VehicleParams, \
    InFlows, NetParams, TrafficLightParams
from flow.controllers import SimCarFollowingController, GridRouter
from flow.envs import TrafficLightGridPOEnv
from flow.core.experiment import Experiment

# agent Parameters
import json
import ray 
try:
    from ray.rllib.agents.agent import get_agent_class
except ImportError:
    from ray.rllib.agents.registry import get_agent_class
from ray.tune import run_experiments
from ray.tune.registry import register_env
from flow.utils.registry import make_create_env
from flow.utils.rllib import FlowParamsEncoder

def getOmgeving(HORIZON):
    sim_params = SumoParams(render=False, sim_step=1,restart_instance=True)
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
    HORIZON = 400               # Time horizon of a single rollout
    flow_params = getOmgeving(HORIZON)
    N_CPUS = 2
    N_ROLLOUTS = 2
    ray.init(
        num_cpus=N_CPUS,
        object_store_memory=50*1024*1024
    )
    alg_run = "PPO"
    agent_cls = get_agent_class(alg_run)
    config = agent_cls._default_config.copy()
    config["num_workers"] = N_CPUS - 1                                          # number of parallel workers
    config["train_batch_size"] = HORIZON * N_ROLLOUTS                           # batch size
    config["gamma"] = 0.9                                                       # discount rate, hoe hoger deze waarde hoe belangrijker de toekomstige rewards zijn
    config["model"].update({"fcnet_hiddens": [16, 16]})                         # size of hidden layers in network
    config["use_gae"] = True                                                    # using generalized advantage estimation
    config["lambda"] = 0.97                                                     # ALPHA?
    config["sgd_minibatch_size"] = min(16 * 1024, config["train_batch_size"])   # stochastic gradient descent
    config["kl_target"] = 0.02                                                  # target KL divergence
    config["num_sgd_iter"] = 10                                                 # number of SGD iterations
    config["horizon"] = HORIZON                                                 # rollout horizon
    # save the flow params for replay
    flow_json = json.dumps(flow_params, cls=FlowParamsEncoder, sort_keys=True,
                        indent=4)                                               # generating a string version of flow_params
    config['env_config']['flow_params'] = flow_json                             # adding the flow_params to config dict
    config['env_config']['run'] = alg_run

    # Call the utility function make_create_env to be able to 
    # register the Flow env for this experiment
    create_env, gym_name = make_create_env(params=flow_params, version=0)

    # Register as rllib env with Gym
    register_env(gym_name, create_env)

    trials = run_experiments({
        flow_params["exp_tag"]: {
            "run": alg_run,
            "env": gym_name,
            "config": {
                **config
            },
            "checkpoint_freq": 1,                   # number of iterations between checkpoints
            "checkpoint_at_end": True,              # generate a checkpoint at the end
            "max_failures": 999,
            "stop": {                               # stopping conditions
                "training_iteration": 5,            # number of iterations to stop after
            },
        },
    })
    # Vragen: => wat zijn de ideale checkpoint_freq en training_iteration? Of moet dit proefondervindelijk gevonden worden
    
    
    '''
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
    '''