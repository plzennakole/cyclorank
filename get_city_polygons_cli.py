import json
import os
import time
import logging
import argparse

import requests

logger = logging.getLogger(__name__)


def main(city_mappings: dict, experiment_name: str = "exp"):
    for country_map in city_mappings:
        for city in city_mappings[country_map]:
            city_name = list(city.keys())[0]
            logger.info(f"Getting polygon for {city_name}")
            try:
                # Get city polygon
                if not os.path.exists(f"{experiment_name}/city_polygons/{city_name.lower()}_polygon.geojson"):
                    city_osm_id = city[city_name]["osm_id"]

                    # hack - first regenerate on server, next call failed if not done this before
                    r = requests.get(f"https://polygons.openstreetmap.fr/?id={city_osm_id}")
                    time.sleep(2)

                    r = requests.get(f"http://polygons.openstreetmap.fr/get_geojson.py?id={city_osm_id}&params=0")

                    logger.info(f"Status code: {r.status_code}, reason: {r.reason}")
                    city_geojson = r.json()
                    time.sleep(3)  # Have mercy on endpoint

                    with open(f"{experiment_name}/city_polygons/{city_name.lower()}_polygon.geojson", "w") as f:
                        json.dump(city_geojson, f)
                else:
                    logger.info(f"Polygon for {city_name} already exists")

                # Save centre coordinates
                centre_coordinates = city[city_name]["centre"]
                city_centre = {
                        "type": "GeometryCollection",
                        "geometries": [
                                {"type": "Point",
                                 "coordinates": [centre_coordinates[0], centre_coordinates[1]]}]}

                with open(f"{experiment_name}/city_polygons/{city_name.lower()}.geojson", "w") as f:
                    json.dump(city_centre, f)

            except Exception as e:
                logger.error(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, default="exp")
    parser.add_argument("--config_path", type=str, default="config/city_conf_czechia.json")
    parser.add_argument("--log_level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    city_mappings = json.load(open(args.config_path))
    os.makedirs(f"{args.experiment_name}/city_polygons", exist_ok=True)

    main(city_mappings, args.experiment_name)
