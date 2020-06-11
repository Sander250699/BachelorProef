# FLOW PARAMS
# network class
from flow.networks import RingNetwork
from flow.core.params import NetParams, InitialConfig
from flow.core.params import VehicleParams
# vehicles dynamic models
from flow.controllers import IDMController, ContinuousRouter
# trainable autonomous vehicle
from flow.controllers import RLController
from flow.networks.ring import ADDITIONAL_NET_PARAMS
# sumo params
from flow.core.params import SumoParams
from flow.core.params import EnvParams
# omgevings variabele
import flow.envs as flowenvs
from flow.envs import WaveAttenuationPOEnv
# RLLIB PARAMS
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
N_CPUS = 2
N_ROLLOUTS = 1
ray.init(
    num_cpus=N_CPUS,
    object_store_memory=50*1024*1024
)


HORIZON = 100
name = "training_example"
network_name = RingNetwork
net_params = NetParams(additional_params=ADDITIONAL_NET_PARAMS)
initial_config = InitialConfig(spacing="uniform", perturbation=1)
vehicles = VehicleParams()
# vehicle configuration 
vehicles.add(
    "human",
    acceleration_controller=(IDMController,{}),
    routing_controller=(ContinuousRouter, {}),
    num_vehicles=21)
vehicles.add(
    "rl",
    acceleration_controller=(RLController, {}),
    routing_controller=(ContinuousRouter,{}),
    num_vehicles=1)
# setting up environment, de gui wordt afgezet om slow down te vermijden
sim_params = SumoParams(sim_step=1, render=False)

#env parameters
env_params = EnvParams(
    #length of one rollout 
    horizon=HORIZON,
    additional_params={
        "max_accel":1,
        "max_decel":1,
        "ring_length":[220,270],
    },
)

#initialize gym environment
print(flowenvs.__all__)
env_name = WaveAttenuationPOEnv

# setting up the flow params
flow_params = dict(
    # name of the experiment
    exp_tag=name,
    # name of the flow environment the experiment is running on
    env_name=env_name,
    # name of the network class the experiment uses
    network=network_name,
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

# configuration and set up for the experiment
alg_run = "PPO"

agent_cls = get_agent_class(alg_run)
config = agent_cls._default_config.copy()
config["num_workers"] = N_CPUS - 1                   # number of parallel workers
config["train_batch_size"] = HORIZON*N_ROLLOUTS      # batch size
config["gamma"]=0.999                                # Discount factor
config["model"].update({"fcnet_hiddens": [16, 16]})  # size of hidden layers in network
config["use_gae"]= True                              # use generalized advantage selection
config["lambda"]= 0.97
config["sgd_minibatch_size"]= min(16 * 1024, config["train_batch_size"])    #stochastic gradient descent
config["kl_target"] = 0.02                           # target KL divergence
config["num_sgd_iter"] = 1                          # number of SGD iterations
config["horizon"] = HORIZON                          # rollout horizon

# save the flow params for replay
flow_json = json.dumps(flow_params, cls=FlowParamsEncoder, sort_keys=True,
                       indent=4)  # generating a string version of flow_params
config['env_config']['flow_params'] = flow_json  # adding the flow_params to config dict
config['env_config']['run'] = alg_run

# Call the utility function make_create_env to be able to 
# register the Flow env for this experiment
create_env, gym_name = make_create_env(params=flow_params, version=0)

# Register as rllib env with Gym
register_env(gym_name, create_env)


# Running the experiment
trails = run_experiments({
    flow_params["exp_tag"]: {
        "run": alg_run,
        "env": gym_name,
        "config": {
            **config
        },
        "checkpoint_freq": 10,           # number of iterations between checkpoints
        "checkpoint_at_end": True,      # generate a checkpoint at the end
        "max_failures": 999,
        "stop":{                        # stopping conditions
            "training_iteration": 10,    # number of iterations to stop after
        },
    },
})