#!/usr/bin/env bash

# default params
EXP_NAME="2014-01-01"
STAGE=1
CITY_CONF="city_conf_czechia.json"

# get shell params form command line

# parsing args
SHORT=e:,s:,c:,h
LONG=stage:,exp-name:,city-conf:,help
OPTS=$(getopt -a -n weather --options $SHORT --longoptions $LONG -- "$@")

eval set -- "$OPTS"

while :; do
  case "$1" in
  -s | --stage)
    STAGE="$2"
    shift 2
    ;;
  -n | --exp-name)
    EXP_NAME="$2"
    shift 2
    ;;
  -c | --city-conf)
    CITY_CONF="$2"
    shift 2
    ;;
  -h | --help)
    "This is a script for running the map analysis pipeline"
    exit 2
    ;;
  --)
    shift
    break
    ;;
  *)
    echo "Unexpected option: $1"
    ;;
  esac
done

echo "STAGE             = ${STAGE}"
echo "EXP_NAME          = $EXP_NAME"
echo "CITY_CONF         = $CITY_CONF"

mkdir -p data/"$EXP_NAME"/extracted_maps

if [ $STAGE -le 1 ]; then
    echo "Stage 1: Downloading and extracting maps"
    python download_and_extract_maps.py "$EXP_NAME" "$CITY_CONF"
fi

if [ $STAGE -le 2 ]; then
    echo "Stage 2: Getting city polygons and sample coordinates"
    # Get city polygons
    mkdir -p ${EXP_NAME}/city_polygons
    python get_city_polygons.py ${EXP_NAME} ${CITY_CONF}
    python routing/sample_coordinates.py ${EXP_NAME} ${CITY_CONF}
fi

if [ $STAGE -le 3 ]; then
    echo "Stage 3: Getting distances for all cities"
    ## 3. Distances
    # get distances for all cities
    # python get_osmium_data.py extracted_maps/Vienna.pbf Vienna

    # for all cities
    for i in $EXP_NAME/extracted_maps/*.pbf; do
        city=$(basename $i .pbf)
        echo $city
        python get_osmium_data.py $i $city "$EXP_NAME"
    done
fi

if [ $STAGE -le 4 ]; then
    echo "Stage 4: Getting decay configs"
    python get_decay_configs.py "$EXP_NAME" "$CITY_CONF"
fi

if [ $STAGE -le 5 ]; then
    echo "Stage 5: Final results"
    python run_map_analysis.py "$EXP_NAME" "$CITY_CONF"
fi

if [ $STAGE -le 6 ]; then
    echo "Stage 6: Convert results to tables"
    python results_to_csv.py "$EXP_NAME" "$CITY_CONF"
fi

if [ $STAGE -le 7 ]; then
    echo "Stage 7: Draw and save maps"
    python draw_maps.py "$EXP_NAME" "$CITY_CONF"
fi