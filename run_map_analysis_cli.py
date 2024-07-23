import os
import sys
import json
import logging
import argparse

from get_osmium_data_cli import osm_for_one_city

logger = logging.getLogger(__name__)


def main(city_mappings: dict, experiment_name: str = "exp"):
    for country_map in city_mappings:
        for city in city_mappings[country_map]:
            city_name = list(city.keys())[0]
            try:
                map_path = f"{experiment_name}/extracted_maps/{city_name}.pbf"
                results_path = f"{experiment_name}/results/{city_name}_decay.json"
                if os.path.exists(results_path):
                    print(f"Skipping {city_name}")
                else:
                    print(f"Working on {city_name}")
                    osm_file = f"{experiment_name}/extracted_maps/{city_name}.pbf"
                    osm_for_one_city(osm_file, city_name, True, experiment_name)
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

    city_mappings = json.load(open(args.config_path))

    os.makedirs(f"{args.experiment_name}/extracted_maps", exist_ok=True)
    os.makedirs(f"{args.experiment_name}/results", exist_ok=True)

    main(args.experiment_name, args.config_path)
