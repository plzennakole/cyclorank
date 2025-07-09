import argparse
import json
import logging
import os.path
import pickle

import matplotlib.pyplot as plt
import tqdm
from pyrosm import OSM

logger = logging.getLogger(__name__)


def main(experiment_name: str, city_mappings: dict, output_path: str, force_rewrite=False):
    exp_date = experiment_name.split("/")[-2] if experiment_name.endswith("/") else experiment_name.split("/")[-1]

    for country_map in city_mappings:
        for city in tqdm.tqdm(city_mappings[country_map]):
            osm_city = list(city.keys())[0]
            logger.info(f"Working on {osm_city}")

            # skip if the file does exist
            if os.path.exists(f"{output_path}/{osm_city}.html") and not force_rewrite:
                logger.info(f"Skipping {osm_city}")
                continue

            filepath = f'{experiment_name}/extracted_maps/{osm_city}.pbf'
            if not os.path.exists(filepath):
                logger.error(f"File {filepath} does not exist")
                continue

            try:
                osm = OSM(filepath)
            except Exception as e:
                logger.error(e)
                continue

            nodes_driving, edges_driving = osm.get_network(nodes=True, network_type="cycling")
            nodes_all, edges_all = osm.get_network(nodes=True, network_type="all")
            drive_net = osm.get_network(network_type="cycling")

            with open(f"{experiment_name}/results/{osm_city}_way_ids.pkl", "rb") as f:
                way_ids = pickle.load(f)

            try:
                subset = drive_net[drive_net["id"].isin(list(way_ids.keys()))]
                lanes = subset[subset["highway"] != "cycleway"]
                segregated_lanes = subset[subset["highway"] != "cycleway"]
            except Exception as e:
                logger.error(e)
                continue

            try:
                m = subset.explore()
                m.save(f"{output_path}/{osm_city}.html")
            except Exception as e:
                logger.error(e)

            try:
                m = lanes.explore()
                m.save(f"{output_path}/{osm_city}_lanes.html")
            except Exception as e:
                logger.error(e)

            try:  # just because of Rumburk with no lanes
                _ = subset.plot(figsize=(15, 15), column="highway", legend=True, linewidth=5)
                plt.title(f"{osm_city} - all ways, {exp_date}")
                plt.savefig(f'{output_path}/{osm_city}.png', dpi=300)
                plt.close()
            except Exception as e:
                logger.error(e)

            # Export the whole road network
            osm = OSM(filepath)
            nodes_driving, edges_driving = osm.get_network(nodes=True, network_type="driving+service")
            nodes_all, edges_all = osm.get_network(nodes=True, network_type="driving+service")
            drive_net = osm.get_network(network_type="driving+service")
            # and save
            # drive_net.to_file(f"{output_path}/{osm_city}_all.geojson", driver="GeoJSON")
            # to HTML
            m = drive_net.explore()
            m.save(f"{output_path}/{osm_city}_whole_network.html")

            # TODO: fix this
            continue

            # Convert the network to a NetworkX graph
            graph = nx.MultiDiGraph()
            graph.add_edges_from(subset[["u", "v", "key"]].to_records(index=False))

            # Calculate the degree distribution of the graph
            degree_sequence = sorted([d for n, d in graph.degree()], reverse=True)
            degree_count = nx.degree_histogram(graph)

            # Plot the degree distribution
            fig, ax = plt.subplots()
            ax.plot(degree_sequence, degree_count, "ro-")
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel("Degree")
            ax.set_ylabel("Count")
            plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, default="exp")
    parser.add_argument("--output_path", type=str, default="exp")
    parser.add_argument("--config_path", type=str, default="config/city_conf_czechia.json")
    parser.add_argument("--force-rewrite", action='store_true')
    parser.add_argument("--log_level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    city_mappings = json.load(open(args.config_path))

    main(args.experiment_name, city_mappings, args.output_path, args.force_rewrite)
