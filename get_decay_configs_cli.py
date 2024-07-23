import argparse
import json
import logging
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np

WEIGHT_AT_UPPER_THRESHOLD = 0.1

logger = logging.getLogger(__name__)


def derive_exponential_decay_params(dists, weight_at_upper_threshold=WEIGHT_AT_UPPER_THRESHOLD):
    """Calibrate decay to put weight 0.1 at 90th percentile of road distance from centroid,
    and 1.0 at 10th percentile"""
    lower_threshold = np.percentile(dists, 10)
    upper_threshold = np.minimum(np.percentile(dists, 90), 15)
    decay_coef = np.log(weight_at_upper_threshold) / (upper_threshold - lower_threshold)

    return {
            "lower_threshold": round(lower_threshold, 1),
            "upper_threshold": round(upper_threshold, 1),
            "decay_coef": round(decay_coef, 2)
    }


def main(city_mappings: dict, experiment_name: str = "exp"):
    for country_map in city_mappings:
        for city in city_mappings[country_map]:

            try:
                city_name = list(city.keys())[0]
                if not (os.path.exists(f"{experiment_name}/results/{city_name}_distances.pkl") and os.path.exists(
                        f"{experiment_name}/results/{city_name}_decay_conf.json")):
                    logger.info(f"{city_name} - working")
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
                    logger.info(f"{city_name} - skipped")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, default="exp")
    parser.add_argument("--config_path", type=str, default="config/city_conf_czechia.json")
    parser.add_argument("--log_level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    city_mappings = json.load(open(args.config_path))
    os.makedirs(f"{args.experiment_name}/results", exist_ok=True)

    main(city_mappings, args.experiment_name)
