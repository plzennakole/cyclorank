import json
import os
import pickle
import sys

import matplotlib.pyplot as plt
import numpy as np

from city_conf import city_mappings

WEIGHT_AT_UPPER_THRESHOLD = 0.1


def derive_exponential_decay_params(dists):
    """Calibrate decay to put weight 0.1 at 90th percentile of road distance from centroid,
    and 1.0 at 10th percentile"""
    lower_threshold = np.percentile(dists, 10)
    upper_threshold = np.minimum(np.percentile(dists, 90), 15)
    decay_coef = np.log(WEIGHT_AT_UPPER_THRESHOLD) / (upper_threshold - lower_threshold)

    return {
        "lower_threshold": round(lower_threshold, 1),
        "upper_threshold": round(upper_threshold, 1),
        "decay_coef": round(decay_coef, 2)
    }


if __name__ == "__main__":

    if len(sys.argv) > 1:
        experiment_name = sys.argv[1]
    else:
        experiment_name = ""
    os.makedirs(f"{experiment_name}/results", exist_ok=True)

    for country_map in city_mappings:
        for city in city_mappings[country_map]:

            try:
                city_name = list(city.keys())[0]
                if not (os.path.exists(f"{experiment_name}/results/{city_name}_distances.pkl") and os.path.exists(
                        f"{experiment_name}/results/{city_name}_decay_conf.json")):
                    print(f"{city_name} - working")
                    with open(f"{experiment_name}/results/{city_name}_distances.pkl", "rb") as f:
                        dists = pickle.load(f)

                    decay_conf = derive_exponential_decay_params(dists)
                    with open(f"{experiment_name}/results/{city_name}_decay_conf.json", "w") as f:
                        json.dump(decay_conf, f)

                    plt.hist(dists, bins=100)
                    plt.axvline(x=decay_conf["lower_threshold"], color="red")
                    plt.axvline(x=decay_conf["upper_threshold"], color="red")
                    plt.title(city_name)
                    plt.savefig(f"{experiment_name}/results/{city_name}_distance_plot.png")
                    plt.close()
                else:
                    print(f"{city_name} - skipped")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
                continue