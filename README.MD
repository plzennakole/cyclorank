Scripts and notebooks for [CycloRank](https://mlumiste.com//projects/cyclorank/)

## 0. Installation

```shell
sudo apt install osmium-tool
pip install osmium
```

## 1. Get maps and data

Get maps and extract cities. 
First, update desired cities in `city_conf.py` and then run:

```shell
mkdir extracted_maps
python download_and_extract_maps.py
```

Get city polygons
```shell
mkdir city_polygons
python get_city_polygons.py
python routing/sample_coordinates.py
```

## 2. Distances

set `decay=False` in `get_osmium_data.py`
and get distances for all cities
```shell
python get_osmium_data.py extracted_maps/Vienna.pbf Vienna

# for all cities
for i in extracted_maps/*.pbf; do
    city=$(basename $i .pbf)
    echo $city
    python get_osmium_data.py $i $city
done
```

then
```shell
python get_decay_configs.py
```

## 3. Final results

```shell
python run_map_analysis.py
```