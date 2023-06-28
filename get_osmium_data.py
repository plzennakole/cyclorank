"""
Extract all objects with an amenity tag from an osm file and list them
with their name and position.
This example shows how geometries from osmium objects can be imported
into shapely using the WKBFactory.
"""
import osmium as o
import numpy as np
import sys
import pickle
import json
import os

from shapely.geometry import shape, Point


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    All args must be of equal length.
    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371 * c
    return km


class AmenityListHandler(o.SimpleHandler):
    def __init__(self, city_centroid, decay_conf=None):
        super(AmenityListHandler, self).__init__()
        self.total_road_length = 0
        self.total_cycling_road_length = 0
        self.total_cycle_lane_length = 0
        self.total_cycle_track_length = 0
        self.total_segregated_cycle_track_length = 0

        self.city_centroid = city_centroid
        self.road_distances_from_centroid = []

        self.parking_counter = 0

        self.decay_conf = decay_conf
        self.way_ids = {}

    def apply_weight_decay(self, road_distance, road_distance_from_centroid):
        effective_distance = np.minimum(np.maximum(road_distance_from_centroid - self.decay_conf["lower_threshold"], 0),
                                        self.decay_conf["upper_threshold"])

        distance_weight = np.exp(
            self.decay_conf["decay_coef"] * effective_distance)

        adj_dist = distance_weight * road_distance
        return adj_dist

    def parse_tag(self, w, tag, tag_values):
        if (tag in w.tags) and (w.tags[tag] in tag_values):
            return True
        else:
            return False

    def parse_way_data_original(self, w):
        """Based on https://wiki.openstreetmap.org/wiki/Bicycle"""
        if "highway" in w.tags:

            highway_length = o.geom.haversine_distance(w.nodes)
            road_lats = [n.lat for n in w.nodes]
            road_lngs = [n.lon for n in w.nodes]
            road_distances = haversine(road_lats, road_lngs, self.city_centroid.y,
                                       self.city_centroid.x)
            road_distance_from_centroid = np.median(road_distances)
            self.road_distances_from_centroid.append(road_distance_from_centroid)

            cycle_lane_length = 0
            cycle_track_length = 0
            segregated_track_length = 0

            # Discount oneways
            if self.parse_tag(w, "oneway", ["yes"]):
                highway_length = 0.5 * highway_length

            # Cycle lanes
            if (
                    # L1a, L1b, M1, M2a, M2b, M2c, B2
                    (self.parse_tag(w, "cycleway", ["lane", "opposite_lane"])) or
                    # L1a, L1b, L2, M1, M2a, M2d, M3b, S2
                    (self.parse_tag(w, "cycleway:right", ["lane", "opposite_lane"])) or
                    # L1a, L1b, M1, M2b, M2d, M3a
                    (self.parse_tag(w, "cycleway:left", ["lane", "opposite_lane"])) or
                    # L1a
                    (self.parse_tag(w, "cycleway:both", ["lane", "opposite_lane"])) or
                    # B1
                    ("bicycle:lanes" in w.tags) or
                    # B3 / other share_busway values
                    (self.parse_tag(w, "cycleway",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    (self.parse_tag(w, "cycleway:right",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    (self.parse_tag(w, "cycleway:left",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    (self.parse_tag(w, "cycleway:both",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    # Sidewalks with explicit cycling
                    (self.parse_tag(w, "sidewalk:both:bicycle", ["designated", "yes"])) or
                    (self.parse_tag(w, "sidewalk:left:bicycle", ["designated", "yes"])) or
                    (self.parse_tag(w, "sidewalk:right:bicycle", ["designated", "yes"])) or
                    (self.parse_tag(w, "sidewalk:bicycle", ["designated", "yes"]))
            ):
                # Discount ways that do not have lane going both ways
                if not (
                        self.parse_tag(w, "cycleway", ["lane"]) or
                        self.parse_tag(w, "cycleway:both", ["lane"]) or
                        (self.parse_tag(w, "cycleway:right", ["lane"]) and self.parse_tag(w, "cycleway:left",
                                                                                          ["lane"])) or
                        (self.parse_tag(w, "cycleway:right", ["lane"]) and self.parse_tag(w, "cycleway:right:oneway",
                                                                                          ["no"])) or
                        (self.parse_tag(w, "cycleway:left", ["lane"]) and self.parse_tag(w, "cycleway:left:oneway",
                                                                                         ["no"]))
                ):
                    cycle_lane_length = highway_length * 0.5
                else:
                    cycle_lane_length = highway_length

            # Cycle tracks
            if (
                    (self.parse_tag(w, "cycleway", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "cycleway:both", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "cycleway:left", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "cycleway:right", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "highway", ["cycleway"])) or
                    (self.parse_tag(w, "highway", ["path", "footway"]) and self.parse_tag(w, "bicycle",
                                                                                          ["designated"])) or
                    (self.parse_tag(w, "cyclestreet", ["yes"])) or
                    (self.parse_tag(w, "bicycle_road", ["yes"]))
            ):
                # Discount oneways
                if (
                        (self.parse_tag(w, "highway", ["cycleway"]) and self.parse_tag(w, "oneway", ["yes"])) or
                        self.parse_tag(w, "oneway:bicycle", ["yes"]) or
                        self.parse_tag(w, "cycleway:right:oneway", ["yes"]) or
                        self.parse_tag(w, "cycleway:left:oneway", ["yes"])
                ):
                    cycle_track_length = 0.5 * highway_length
                else:
                    cycle_track_length = highway_length

                if self.parse_tag(w, "segregated", ["yes"]):
                    segregated_track_length = cycle_track_length

            if True:
                if cycle_lane_length + cycle_track_length > 0:
                    self.way_ids[w.id] = {"raw_distance": cycle_lane_length + cycle_track_length,
                                          "dist_from_centr": road_distance_from_centroid}

            if self.decay_conf:
                highway_length = self.apply_weight_decay(highway_length, road_distance_from_centroid)
                cycle_lane_length = self.apply_weight_decay(cycle_lane_length, road_distance_from_centroid)
                cycle_track_length = self.apply_weight_decay(cycle_track_length, road_distance_from_centroid)
                segregated_track_length = self.apply_weight_decay(segregated_track_length, road_distance_from_centroid)

            if True:
                if cycle_lane_length + cycle_track_length > 0:
                    self.way_ids[w.id]["weighted_distance"] = cycle_lane_length + cycle_track_length

            self.total_road_length += highway_length
            self.total_cycle_lane_length += cycle_lane_length
            self.total_cycle_track_length += cycle_track_length
            self.total_segregated_cycle_track_length += segregated_track_length
            self.total_cycling_road_length += cycle_lane_length + cycle_track_length

    def parse_way_data(self, w):
        """CZE version 1.0
            Based on https://wiki.openstreetmap.org/wiki/Bicycle"""
        if "highway" in w.tags:

            highway_length = o.geom.haversine_distance(w.nodes)
            road_lats = [n.lat for n in w.nodes]
            road_lngs = [n.lon for n in w.nodes]
            road_distances = haversine(road_lats, road_lngs, self.city_centroid.y,
                                       self.city_centroid.x)
            road_distance_from_centroid = np.median(road_distances)
            self.road_distances_from_centroid.append(road_distance_from_centroid)

            cycle_lane_length = 0
            cycle_track_length = 0
            segregated_track_length = 0

            # Discount one-ways
            if self.parse_tag(w, "oneway", ["yes"]):
                highway_length = 0.5 * highway_length

            # Cycle lanes
            if (
                    # L1a, L1b, M1, M2a, M2b, M2c, B2
                    (self.parse_tag(w, "cycleway", ["lane", "opposite_lane", "soft_lane"])) or
                    # L1a, L1b, L2, M1, M2a, M2d, M3b, S2
                    (self.parse_tag(w, "cycleway:right", ["lane", "opposite_lane", "soft_lane"])) or
                    # L1a, L1b, M1, M2b, M2d, M3a
                    (self.parse_tag(w, "cycleway:left", ["lane", "opposite_lane", "soft_lane"])) or
                    # L1a
                    (self.parse_tag(w, "cycleway:both", ["lane", "opposite_lane", "soft_lane"])) or
                    # B1
                    ("bicycle:lanes" in w.tags) or
                    # B3 / other share_busway values
                    (self.parse_tag(w, "cycleway",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    (self.parse_tag(w, "cycleway:right",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    (self.parse_tag(w, "cycleway:left",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    (self.parse_tag(w, "cycleway:both",
                                    ["share_busway", "opposite_share_busway", "shoulder", "shared_lane"])) or
                    # Sidewalks with explicit cycling
                    (self.parse_tag(w, "sidewalk:both:bicycle", ["designated", "yes"])) or
                    (self.parse_tag(w, "sidewalk:left:bicycle", ["designated", "yes"])) or
                    (self.parse_tag(w, "sidewalk:right:bicycle", ["designated", "yes"])) or
                    (self.parse_tag(w, "sidewalk:bicycle", ["designated", "yes"]))
            ):
                # Discount ways that do not have lane going both ways
                if not (
                        self.parse_tag(w, "cycleway", ["lane"]) or
                        self.parse_tag(w, "cycleway:both", ["lane"]) or
                        (self.parse_tag(w, "cycleway:right", ["lane"]) and self.parse_tag(w, "cycleway:left",
                                                                                          ["lane"])) or
                        (self.parse_tag(w, "cycleway:right", ["lane"]) and self.parse_tag(w, "cycleway:right:oneway",
                                                                                          ["no"])) or
                        (self.parse_tag(w, "cycleway:left", ["lane"]) and self.parse_tag(w, "cycleway:left:oneway",
                                                                                         ["no"]))
                ):
                    cycle_lane_length = highway_length * 0.5
                else:
                    cycle_lane_length = highway_length

                # bus lines are not segregated, weight them 0.2
                if self.parse_tag(w, "cycleway", ["share_busway", "opposite_share_busway"]):
                    cycle_lane_length = cycle_lane_length * 0.2

            # Cycle tracks
            if (
                    (self.parse_tag(w, "cycleway", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "cycleway:both", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "cycleway:left", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "cycleway:right", ["track", "opposite_track"])) or
                    (self.parse_tag(w, "highway", ["cycleway"])) or
                    (self.parse_tag(w, "highway", ["path", "footway"]) and  # highway=path is not always a cycleway
                        (self.parse_tag(w, "bicycle", ["designated"]) and self.parse_tag(w, "bicycle", ["yes"]))) or
                    (self.parse_tag(w, "cyclestreet", ["yes"])) or
                    (self.parse_tag(w, "bicycle_road", ["yes"])) or
                    (self.parse_tag(w, "highway", ["pedestrian"]) and self.parse_tag(w, "bicycle", ["yes"])) or
                    (self.parse_tag(w, "highway", ['pedestrian']) and self.parse_tag(w, 'bicycle', ["designated"])) or
                    # highway = footway and bicycle = yes
                    (self.parse_tag(w, "highway", ["footway"]) and self.parse_tag(w, "bicycle", ["yes"])) or
                    # oneway = yes and oneway:bicycle = no
                    (self.parse_tag(w, "oneway", ["yes"]) and self.parse_tag(w, "oneway:bicycle", ["no"])) or
                    # highway = footway and bicycle = designated
                    (self.parse_tag(w, "highway", ["footway"]) and self.parse_tag(w, "bicycle", ["designated"])) or
                    # highway=service + bicycle=yes
                    (self.parse_tag(w, "highway", ["service"]) and self.parse_tag(w, "bicycle", ["yes"])) or
                    # highway=track + bicycle=yes
                    (self.parse_tag(w, "highway", ["track"]) and self.parse_tag(w, "bicycle", ["yes"]))
            ):
                # Discount oneways
                if (
                        (self.parse_tag(w, "highway", ["cycleway"]) and self.parse_tag(w, "oneway", ["yes"])) or
                        self.parse_tag(w, "oneway:bicycle", ["yes"]) or
                        self.parse_tag(w, "cycleway:right:oneway", ["yes"]) or
                        self.parse_tag(w, "cycleway:left:oneway", ["yes"])
                ):
                    cycle_track_length = 0.5 * highway_length
                else:
                    cycle_track_length = highway_length

                if self.parse_tag(w, "segregated", ["yes"]):
                    segregated_track_length = cycle_track_length

            # Bicycle dismount
            if (
                    self.parse_tag(w, "highway", ["no", "dismount"])
                ):
                cycle_track_length = 0  # Dismounting is not cycling :)

            if True:
                if cycle_lane_length + cycle_track_length > 0:
                    self.way_ids[w.id] = {"raw_distance": cycle_lane_length + cycle_track_length,
                                          "dist_from_centr": road_distance_from_centroid}

            if self.decay_conf:
                highway_length = self.apply_weight_decay(highway_length, road_distance_from_centroid)
                cycle_lane_length = self.apply_weight_decay(cycle_lane_length, road_distance_from_centroid)
                cycle_track_length = self.apply_weight_decay(cycle_track_length, road_distance_from_centroid)
                segregated_track_length = self.apply_weight_decay(segregated_track_length, road_distance_from_centroid)

            if True:
                if cycle_lane_length + cycle_track_length > 0:
                    self.way_ids[w.id]["weighted_distance"] = cycle_lane_length + cycle_track_length

            self.total_road_length += highway_length
            self.total_cycle_lane_length += cycle_lane_length
            self.total_cycle_track_length += cycle_track_length
            self.total_segregated_cycle_track_length += segregated_track_length
            self.total_cycling_road_length += cycle_lane_length + cycle_track_length

    def way(self, w):
        self.parse_way_data(w)

    def node(self, n):
        if ("amenity" in n.tags) and n.tags["amenity"] == "bicycle_parking":
            self.parking_counter += 1


def main(osmfile, city_name, decay=False, experiment_name=""):
    with open(f"{experiment_name}/city_polygons/{city_name.lower()}.geojson") as f:
        city_json = json.load(f)

    city_polygon = shape(city_json)
    city_centroid = Point((city_polygon.centroid.y, city_polygon.centroid.x))

    if decay:
        with open(f"{experiment_name}/results/{city_name}_decay_conf.json", "r") as f:
            decay_conf = json.load(f)
            print(f"Using decay conf: {decay_conf}")
    else:
        decay_conf = None

    handler = AmenityListHandler(city_centroid, decay_conf=decay_conf)
    handler.apply_file(osmfile, locations=True)

    # Multiply distances by 2 to count both ways
    summary = {
        "city_name": city_name,
        "total_road_length": (2 * handler.total_road_length) / 1000,
        "total_cycling_road_length": (2 * handler.total_cycling_road_length) / 1000,
        "total_cycle_lane_length": (2 * handler.total_cycle_lane_length) / 1000,
        "total_cycle_track_length": (2 * handler.total_cycle_track_length) / 1000,
        "total_segregated_cycle_track_length": (2 * handler.total_segregated_cycle_track_length) / 1000,
        "parking_counter": handler.parking_counter
    }

    print(summary)

    if decay:
        with open(f"{experiment_name}/results/{city_name}_decay.json", "w") as f:
            json.dump(summary, f)
    else:
        with open(f"{experiment_name}/results/{city_name}.json", "w") as f:
            json.dump(summary, f)

    with open(f"{experiment_name}/results/{city_name}_distances.pkl", "wb") as f:
        pickle.dump(handler.road_distances_from_centroid, f)

    if True:
        with open(f"{experiment_name}/results/{city_name}_way_ids.pkl", "wb") as f:
            pickle.dump(handler.way_ids, f)

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python %s <osmfile> <city_name> <output-dir>" % sys.argv[0])
        sys.exit(-1)

    osmfile = sys.argv[1]
    city_name = sys.argv[2]
    experiment_name = sys.argv[3]

    os.makedirs(f"{experiment_name}/results", exist_ok=True)

    exit(main(osmfile, city_name, decay=False, experiment_name=experiment_name))
