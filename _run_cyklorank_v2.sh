#!/usr/bin/env bash

set -eu
set -o pipefail

# default params
EXP_NAME="data/2024-07-22"
STAGE=1
LOGLEVEL="INFO"

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

if [ $STAGE -le 1 ]; then
    echo "Stage 1: Downloading and extracting maps"
    python download_and_extract_maps_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    python download_and_extract_maps_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
fi

if [ $STAGE -le 2 ]; then
    echo "Stage 2: Getting city polygons and sample coordinates"
    # Get city polygons for Czechia
    python get_city_polygons_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    python routing/sample_coordinates.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    # Get city polygons for Europe
    python get_city_polygons_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
    python routing/sample_coordinates.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
fi

if [ $STAGE -le 3 ]; then
    echo "Stage 3: Getting distances for all cities"
    python get_osmium_data_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    python get_osmium_data_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
fi

if [ $STAGE -le 4 ]; then
    echo "Stage 4: Getting decay configs"
    python get_decay_configs_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    python get_decay_configs_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
fi

if [ $STAGE -le 5 ]; then
    echo "Stage 5: Final results"
    python run_map_analysis_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    python run_map_analysis_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
fi

if [ $STAGE -le 6 ]; then
    echo "Stage 6: Convert results to tables"
    # all
    python results_to_csv_cli.py --experiment_name "$EXP_NAME" --config_path config/city_conf_czechia.json config/city_conf_europe.json --log_level $LOGLEVEL
    # only CZ
    python results_to_csv_cli.py --experiment_name "$EXP_NAME/Czechia" --config_path config/city_conf_czechia.json --log_level $LOGLEVEL
    # only Europe
    python results_to_csv_cli.py --experiment_name "$EXP_NAME/Europe" --config_path config/city_conf_europe.json --log_level $LOGLEVEL
fi

if [ $STAGE -le 7 ]; then
    echo "Stage 7: Draw and save maps"
    python draw_maps_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL
    python draw_maps_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL
fi
