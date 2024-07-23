import argparse
import json
import logging
import os
import subprocess

GEOFABRIK_ROOT_PATH = "https://download.geofabrik.de/"

logger = logging.getLogger(__name__)


def download_map(geofabrik_path: str, experiment_name: str = "exp") -> str:
    full_path = GEOFABRIK_ROOT_PATH + geofabrik_path
    subprocess.run(["wget", "-P", f"{experiment_name}/full_maps", full_path])
    filename = geofabrik_path.split("/")[-1]
    return filename


def extract_map(city_name, relation_id, full_map_path, experiment_name=""):
    logger.info(f"Working on map for {city_name} - id {relation_id}")
    logger.info("Extracting boundary")
    subprocess.run(
        f"osmium getid -r -t {experiment_name}/full_maps/{full_map_path} r{relation_id} -o {experiment_name}/extracted_maps/{city_name}_boundary.pbf",
        shell=True)
    logger.info("Extracting city")
    subprocess.run(f"osmium extract -p {experiment_name}/extracted_maps/{city_name}_boundary.pbf "
                   f"{experiment_name}/full_maps/{full_map_path} -o {experiment_name}/extracted_maps/{city_name}.pbf",
                   shell=True)

    if os.path.exists(f"{experiment_name}/extracted_maps/{city_name}.pbf"):
        logger.info("Removing boundary file")
        subprocess.run(f"rm {experiment_name}/extracted_maps/{city_name}_boundary.pbf", shell=True)


def main(country_to_cities: dict, experiment_name: str = "exp", remove_country_map=True):
    for country_map in country_to_cities:
        try:
            missing_cities = []
            for city in country_to_cities[country_map]:
                city_name = list(city.keys())[0]

                if not os.path.exists(f"{experiment_name}/extracted_maps/{city_name}.pbf"):
                    missing_cities.append(city)

            if missing_cities:
                logger.info(f"Map: {country_map}")
                logger.info(f"Missing cities: {missing_cities}")
                full_map_path = country_map.split("/")[-1]
                if not os.path.exists(f"{experiment_name}/full_maps/{full_map_path}"):
                    full_map_path = download_map(country_map, experiment_name=experiment_name)

                for missing_city in missing_cities:
                    for missing_city_name in missing_city:
                        osm_id = missing_city[missing_city_name]["osm_id"]
                        extract_map(missing_city_name, osm_id, full_map_path=full_map_path,
                                    experiment_name=experiment_name)

                logger.warning("Removing country map")
                if "czech" not in full_map_path.lower() and remove_country_map:
                    subprocess.run(f"rm {experiment_name}/full_maps/{full_map_path}", shell=True)

        # TODO: add more specific exceptions
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
    parser.add_argument("--remove_country_map", type=bool, default=True)
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    city_mappings = json.load(open(args.config_path))
    os.makedirs(f"{args.experiment_name}/full_maps", exist_ok=True)
    os.makedirs(f"{args.experiment_name}/extracted_maps", exist_ok=True)

    main(city_mappings, args.experiment_name, args.remove_country_map)
