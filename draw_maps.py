import pickle
import sys
import json

from pyrosm import OSM

if __name__ == "__main__":

    if len(sys.argv) > 1:
        experiment_name = sys.argv[1]
        config_path = sys.argv[2]
        city_mappings = json.load(open(config_path))
    else:
        osm_city = "Plzeň"
        experiment_name = "data/2014-01-01/"
        city_mappings = json.load(open("city_conf_czechia.json"))

    for country_map in city_mappings:
        for city in city_mappings[country_map]:
            osm_city = list(city.keys())[0]

            filepath = f'{experiment_name}/extracted_maps/{osm_city}.pbf'
            osm = OSM(filepath)
            nodes_driving, edges_driving = osm.get_network(nodes=True, network_type="cycling")
            nodes_all, edges_all = osm.get_network(nodes=True, network_type="all")
            drive_net = osm.get_network(network_type="cycling")

            with open(f"{experiment_name}/results/{osm_city}_way_ids.pkl", "rb") as f:
                way_ids = pickle.load(f)

            subset = drive_net[drive_net["id"].isin(list(way_ids.keys()))]
            lanes = subset[subset["highway"] != "cycleway"]
            segregated_lanes = subset[subset["highway"] != "cycleway"]

            subset.plot(figsize=(35, 35), column="highway", legend=True)

            m = subset.explore()
            m.save(f"{experiment_name}/{osm_city}.html")

            m = lanes.explore()
            m.save(f"{experiment_name}/{osm_city}_lanes.html")
