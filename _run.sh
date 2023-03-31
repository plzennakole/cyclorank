#!/usr/bin/env bash

# EXP_NAME="2014-01-01"
EXP_NAME=$1

mkdir -p data/"$EXP_NAME"/extracted_maps

## 1. Get maps and data
python download_and_extract_maps.py ${EXP_NAME}

# Get city polygons
mkdir -p ${EXP_NAME}/city_polygons
python get_city_polygons.py ${EXP_NAME}
python routing/sample_coordinates.py ${EXP_NAME}

## 2. Distances
# get distances for all cities
# python get_osmium_data.py extracted_maps/Vienna.pbf Vienna

# for all cities
for i in $EXP_NAME/extracted_maps/*.pbf; do
    city=$(basename $i .pbf)
    echo $city
    python get_osmium_data.py $i $city "$EXP_NAME"
done

python get_decay_configs.py "$EXP_NAME"

## 3. Final results
python run_map_analysis.py "$EXP_NAME"
