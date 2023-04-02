import os
import subprocess
import sys
import json

country_to_cities = json.load(open("city_conf_czechia.json"))
GEOFABRIK_ROOT_PATH = "https://download.geofabrik.de/"

def download_map(geofabrik_path, experiment_name=""):
    full_path = GEOFABRIK_ROOT_PATH + geofabrik_path
    subprocess.run(["wget", "-P", f"{experiment_name}/full_maps", full_path])
    filename = geofabrik_path.split("/")[-1]
    return filename


def extract_map(city_name, relation_id, full_map_path, experiment_name=""):
    print(f"Working on map for {city_name} - id {relation_id}")
    print("Extracting boundary")
    subprocess.run(f"osmium getid -r -t {experiment_name}/full_maps/{full_map_path} r{relation_id} -o {experiment_name}/extracted_maps/{city_name}_boundary.pbf",
        shell=True)
    print("Extracting city")
    subprocess.run(f"osmium extract -p {experiment_name}/extracted_maps/{city_name}_boundary.pbf "
                   f"{experiment_name}/full_maps/{full_map_path} -o {experiment_name}/extracted_maps/{city_name}.pbf",
        shell=True)

    if os.path.exists(f"{experiment_name}/extracted_maps/{city_name}.pbf"):
        print("Removing boundary file")
        subprocess.run(f"rm {experiment_name}/extracted_maps/{city_name}_boundary.pbf", shell=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        experiment_name = sys.argv[1]
        config_path = sys.argv[2]
        city_mappings = json.load(open(config_path))
    else:
        experiment_name = ""
        city_mappings = json.load(open("city_conf_czechia.json"))
    os.makedirs(f"{experiment_name}/full_maps", exist_ok=True)
    os.makedirs(f"{experiment_name}/extracted_maps", exist_ok=True)

    for country_map in country_to_cities:
        try:
            missing_cities = []
            for city in country_to_cities[country_map]:
                city_name = list(city.keys())[0]

                if not os.path.exists(f"{experiment_name}/extracted_maps/{city_name}.pbf"):
                    missing_cities.append(city)

            if missing_cities:
                print(f"Map: {country_map}")
                print(f"Missing cities: {missing_cities}")
                full_map_path = country_map.split("/")[-1]
                if not os.path.exists(f"{experiment_name}/full_maps/{full_map_path}"):
                    full_map_path = download_map(country_map, experiment_name=experiment_name)

                for missing_city in missing_cities:
                    for missing_city_name in missing_city:
                        osm_id = missing_city[missing_city_name]["osm_id"]
                        extract_map(missing_city_name, osm_id, full_map_path=full_map_path, experiment_name=experiment_name)

                print("Removing country map")
                if "czech" not in full_map_path.lower():
                    subprocess.run(f"rm {experiment_name}/full_maps/{full_map_path}", shell=True)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(e)
            continue
