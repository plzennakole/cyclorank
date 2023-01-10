#!/usr/bin/env bash

EXP_NAME="2023-01-10"

mkdir -p data/$EXP_NAME/extracted_maps

## 1. Get maps and data
python download_and_extract_maps.py data/${EXP_NAME}

# Get city polygons
mkdir data/${EXP_NAME}/city_polygons
python get_city_polygons.py data/${EXP_NAME}
python routing/sample_coordinates.py data/${EXP_NAME}

## 2. Distances
# get distances for all cities
# python get_osmium_data.py extracted_maps/Vienna.pbf Vienna

# for all cities
for i in data/$EXP_NAME/extracted_maps/*.pbf; do
    city=$(basename $i .pbf)
    echo $city
    python get_osmium_data.py $i $city data/$EXP_NAME/
done

python get_decay_configs.py data/$EXP_NAME

## 3. Final results
python run_map_analysis.py data/$EXP_NAME