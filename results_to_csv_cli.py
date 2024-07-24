import argparse
import json
import logging
from functools import partial

import pandas as pd
import pyproj
import shapely.ops as ops
from shapely.geometry import shape

logger = logging.getLogger(__name__)


def find_polygon_area(geojson):
    geom = shape(geojson)
    geom_area = ops.transform(
            partial(
                    pyproj.transform,
                    pyproj.Proj(init='EPSG:4326'),
                    pyproj.Proj(
                            proj='aea',
                            lat_1=geom.bounds[1],
                            lat_2=geom.bounds[3]
                    )
            ),
            geom)
    return geom_area.area / 1e6


def generate_html(dataframe: pd.DataFrame):
    # get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id="table")
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <body>
    {table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#table').DataTable({{
                // paging: false,    
                // scrollY: 400,
            }});
        }});
    </script>
    </body>
    </html>
    """
    # return the html
    return html


def main(city_mappings: dict, experiment_name: str = "exp"):
    city_records = []
    for country_map in city_mappings:
        for city in city_mappings[country_map]:
            city_name = list(city.keys())[0]
            osm_id = city[city_name]["osm_id"]
            try:
                with open(f"{experiment_name}/results/{city_name}.json", "r") as f:
                    city_record = json.load(f)

                with open(f"{experiment_name}/city_polygons/{city_name.lower()}_polygon.geojson") as f:
                    city_polygon = json.load(f)

                city_record["osm_id"] = osm_id
                city_record["area_km2"] = find_polygon_area(city_polygon)
                city_records.append(city_record)
                logger.info(f"Processed {city_name}")
            except Exception as e:
                print(f"Error: {e}")
                continue

    df = pd.DataFrame(city_records)

    city_records_with_decay = []
    for country_map in city_mappings:
        for city in city_mappings[country_map]:
            city_name = list(city.keys())[0]
            osm_id = city[city_name]["osm_id"]
            try:
                with open(f"{experiment_name}/results/{city_name}_decay.json", "r") as f:
                    city_record = json.load(f)

                with open(f"{experiment_name}/city_polygons/{city_name.lower()}_polygon.geojson") as f:
                    city_polygon = json.load(f)

                city_record["osm_id"] = osm_id
                city_record["area_km2"] = find_polygon_area(city_polygon)
                city_records_with_decay.append(city_record)
            except Exception as e:
                logger.error(f"Error: {e}")
                continue

    df_decay = pd.DataFrame(city_records_with_decay)

    df["overall_road_length"] = df["total_cycling_road_length"] + df["total_road_length"]
    df_decay["overall_road_length"] = df_decay["total_cycling_road_length"] + df_decay["total_road_length"]

    df["cycle_road_share"] = df["total_cycling_road_length"] / df["overall_road_length"]
    df_decay["cycle_road_share"] = df_decay["total_cycling_road_length"] / df_decay["overall_road_length"]

    df["cycle_track_share"] = df["total_cycle_track_length"] / df["overall_road_length"]
    df_decay["cycle_track_share"] = df_decay["total_cycle_track_length"] / df_decay["overall_road_length"]

    df["cycle_lane_share"] = df["total_cycle_lane_length"] / df["overall_road_length"]
    df_decay["cycle_lane_share"] = df_decay["total_cycle_lane_length"] / df_decay["overall_road_length"]

    df["segregated_cycle_track_share"] = df["total_segregated_cycle_track_length"] / df["overall_road_length"]
    df_decay["segregated_cycle_track_share"] = df_decay["total_segregated_cycle_track_length"] / df_decay[
        "overall_road_length"]

    df["rank_cycle_road_share"] = df["cycle_road_share"].rank(ascending=False).astype(int)
    df["rank_cycle_track_share"] = df["cycle_track_share"].rank(ascending=False).astype(int)
    df["rank_segregated_cycle_track_share"] = df["segregated_cycle_track_share"].rank(ascending=False).astype(int)

    df_decay["rank_cycle_road_share"] = df_decay["cycle_road_share"].rank(ascending=False).astype(int)
    df_decay["rank_cycle_track_share"] = df_decay["cycle_track_share"].rank(ascending=False).astype(int)
    df_decay["rank_segregated_cycle_track_share"] = df_decay["segregated_cycle_track_share"].rank(
            ascending=False).astype(
            int)

    merged = df.merge(df_decay, on=["city_name", "osm_id", "area_km2"], suffixes=["", "_decayed"])

    # merged["overall_score"] = merged["cycle_road_share_decayed"] * merged["cycle_track_share_decayed"] #* merged[
    #     "segregated_cycle_track_share_decayed"]
    # merged["overall_score"] = merged["cycle_road_share"] * merged["segregated_cycle_track_share"]
    merged["overall_score"] = merged["cycle_road_share_decayed"]
    merged["overall_rank"] = merged["overall_score"].rank(ascending=False).astype(int)

    merged["parking_per_km2"] = merged['parking_counter'] / merged["area_km2"]

    merged["rank_diff"] = merged["rank_cycle_road_share"] - merged["rank_cycle_road_share_decayed"]

    final = merged[
        ["city_name",
         "osm_id",
         "area_km2",
         "total_road_length",
         "total_cycling_road_length",
         "total_cycle_track_length",
         "total_cycle_lane_length",
         "total_segregated_cycle_track_length",
         "cycle_road_share",
         "cycle_track_share",
         "cycle_lane_share",
         "segregated_cycle_track_share",
         "cycle_road_share_decayed",
         "cycle_track_share_decayed",
         "segregated_cycle_track_share_decayed",
         "parking_per_km2",
         "overall_rank"]].round(3).rename(columns={
            "city_name": "City name",
            "osm_id": "OSM id",
            "area_km2": "Area (km2)",
            "total_road_length": "Navigable road length (km)",
            "total_cycling_road_length": "Navigable bike road length (km)",
            "total_cycle_track_length": "Cycle track length (km)",
            "total_cycle_lane_length": "Cycle lane length (km)",
            "total_segregated_cycle_track_length": "Segregated cycle track length (km)",
            "cycle_road_share": "Cycle road share",
            "cycle_track_share": "Cycle track share",
            "cycle_lane_share": "Cycle lane share",
            "segregated_cycle_track_share": "Segregated track share",
            "cycle_road_share_decayed": "Cycle road share (weighted)",
            "cycle_track_share_decayed": "Cycle track share (weighted)",
            "segregated_cycle_track_share_decayed": "Segregated track share (weighted)",
            "parking_per_km2": "Parking spaces (per km2)",
            "overall_rank": "Rank"
    })

    final.sort_values("Rank", ascending=True)

    with open(f"{experiment_name}/_table.cs.html", "wt") as fout:
        fout.write(final.sort_values("Rank", ascending=True).to_html(index=False))

    # write to CSV table
    final.sort_values("Rank", ascending=True).to_csv(f"{experiment_name}/_table.cs.csv", index=False)

    html = generate_html(final.sort_values("Rank", ascending=True))
    # write the HTML content to an HTML file
    with open(f"{experiment_name}/_table.cs.sortable.html", "wt") as fout:
        fout.write(html)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, default="exp")
    parser.add_argument("--config_path", type=str, nargs="+", default="config/city_conf_czechia.json")
    parser.add_argument("--log_level", type=str, default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    # switch off FutureWarning for pyproj
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    # combine multiple config files to one
    city_mappings = json.load(open(args.config_path[0]))
    for config_path in args.config_path[1:]:
        # do not overwrite the first one
        _data = json.load(open(config_path))
        for country_map in _data:
            if country_map not in city_mappings:
                city_mappings[country_map] = _data[country_map]
            else:
                city_mappings[country_map].extend(_data[country_map])

    main(city_mappings, args.experiment_name)
