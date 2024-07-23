import argparse
import json
import logging
import os
import pickle
import random

from routing.sample_coordinates import NUM_POINTS
from routing.sample_coordinates import NUM_ROUTES
from routing.sample_coordinates import load_city_shapes
from routing.sample_coordinates import random_points_within

logger = logging.getLogger(__name__)


def main(city_mappings: dict, experiment_name: str = "exp"):
    for country_map in city_mappings:
        for city in city_mappings[country_map]:
            city_name = list(city.keys())[0]
            try:
                if not os.path.exists(f"{experiment_name}/routing/routes/{city_name}.p"):
                    logger.info(f"Generating routes for {city_name}")
                    shapes = load_city_shapes(city_name, experiment_name=experiment_name)
                    points = random_points_within(circle_polygon=shapes["circle_polygon"],
                                                  city_polygon=shapes["city_polygon"],
                                                  num_points=NUM_POINTS)
                    routes = []
                    for i in range(NUM_ROUTES):
                        start_point = random.choice(points)
                        end_point = random.choice(points)
                        routes.append(
                                (
                                        float(start_point.y), float(start_point.x), float(end_point.y),
                                        float(end_point.x)))

                    with open(f"{experiment_name}/routing/routes/{city_name}.p", "wb") as f:
                        pickle.dump(routes, f)
            # TODO: Add exception handling
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(e)
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, default="exp")
    parser.add_argument("--config_path", type=str, default="config/city_conf_czechia.json")
    parser.add_argument("--log_level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    city_mappings = json.load(open(args.config_path))
    os.makedirs(f"{args.experiment_name}/routing/routes", exist_ok=True)

    main(city_mappings, args.experiment_name)
