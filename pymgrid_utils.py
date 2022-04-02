import pickle
import random
import numpy as np
import pandas as pd
from copy import copy
from pymgrid import MicrogridGenerator as m_gen
from pymgrid.Environments.ScenarioEnvironment import CSPLAScenarioEnvironment



def get_microgrid(id=1, export_price_factor=0):
    # Create 25 defaults microgrids
    env = m_gen.MicrogridGenerator(nb_microgrid=25)
    pymgrid25 = env.load("pymgrid25")
    microgrids_25 = pymgrid25.microgrids

    # Select the 1 microgrid
    mg = microgrids_25[1]

    # Modify export prices to not be 0
    mg._grid_price_export[0] = mg._grid_price_import[0] * 0.0
    mg._grid_status_ts[0] = pd.Series(np.ones(len(mg._grid_status_ts)))

    return mg


def get_environments(pv_factor=1.0, action_design="original"):
    mg = get_microgrid()
    mg_train = copy(mg)
    mg_test = copy(mg)
    starts = list(range(0, 6759, 2000))

    mg_env_train = CSPLAScenarioEnvironment(
        starts,
        2000,
        {"microgrid": mg_train},
        action_design="original",
        pv_factor=pv_factor,
    )

    mg_env_eval = CSPLAScenarioEnvironment(
        [0],
        8760,
        {"microgrid": mg_test},
        action_design=action_design,
        pv_factor=pv_factor,
    )

    return mg_env_train, mg_env_eval


def get_environments_for_cluster(
    cluster,
    pv_factor=1.0,
    starts_file="clusteringResultPymgrid25_configcfgN10k200_MERGED_0startsLengthsClIds.pkl",
    action_design="original",
    seed=42,
):
    mg = get_microgrid()
    mg_train = copy(mg)
    mg_test = copy(mg)
    object = read_pickle(f"data/{starts_file}")[0]
    cluster_ids = object["clusteringIds"]
    starts = object["piceStarts"]
    max_cluster = max(cluster_ids)
    if cluster > max_cluster:
        raise ValueError(
            f"Cluster {cluster} does not exist, max cluster is {max_cluster}"
        )

    # Get the whole starts list for the current cluster
    starts_cluster = starts[cluster_ids == cluster]

    # Split the starts list between train and test
    train_starts, test_starts = train_test_split(starts_cluster, seed=42)
    mg_env_train = CSPLAScenarioEnvironment(
        train_starts,
        1000,
        {"microgrid": mg},
        action_design=action_design,
        pv_factor=pv_factor,
    )
    mg_env_eval = CSPLAScenarioEnvironment(
        test_starts,
        1000,
        {"microgrid": mg},
        action_design=action_design,
        pv_factor=pv_factor,
    )

    return mg_env_train, mg_env_eval


def read_pickle(file):
    objects = []
    with (open(file, "rb")) as openfile:
        while True:
            try:
                objects.append(pickle.load(openfile))
            except EOFError:
                break
        return objects


def train_test_split(list_in, ratio=0.7, seed=None):
    if seed is not None:
        random.seed(seed)
    random.shuffle(list_in)
    split_idx = int(ratio * len(list_in))
    train = list_in[:split_idx]
    test = list_in[split_idx:]
    return train, test
