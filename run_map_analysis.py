import os
import sys
import json

from get_osmium_data import main

if __name__ == "__main__":
    if len(sys.argv) > 1:
        experiment_name = sys.argv[1]
        config_path = sys.argv[2]
        city_mappings = json.load(open(config_path))
    else:
        experiment_name = ""
        city_mappings = json.load(open("city_conf_czechia.json"))
    os.makedirs(f"{experiment_name}/extracted_maps", exist_ok=True)
    os.makedirs(f"{experiment_name}/results", exist_ok=True)

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
                    main(map_path, city_name, decay=True, experiment_name=experiment_name)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e)
                continue
