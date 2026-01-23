#!/usr/bin/env bash

set -eu
set -o pipefail

# default params
EXP_NAME="data/2026-01-21"
STAGE=1
LOGLEVEL="INFO"

# get shell params form command line

# parsing args (manual parsing for macOS compatibility)
while [[ $# -gt 0 ]]; do
  case "$1" in
  -s|--stage)
    STAGE="$2"
    shift 2
    ;;
  -n|--exp-name)
    EXP_NAME="$2"
    shift 2
    ;;
  -h|--help)
    echo "This is a script for running the map analysis pipeline"
    echo "Usage: $0 [OPTIONS]"
    echo "  -s, --stage STAGE        Start from stage STAGE (default: 1)"
    echo "  -n, --exp-name NAME      Experiment name/path (default: data/2026-01-21)"
    echo "  -h, --help               Show this help message"
    exit 0
    ;;
  --)
    shift
    break
    ;;
  -*)
    echo "Unknown option: $1"
    exit 1
    ;;
  *)
    break
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
    # default method now is cze_v1.1
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
    python run_map_analysis_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" --log_level $LOGLEVEL --force-rewrite
    python run_map_analysis_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" --log_level $LOGLEVEL --force-rewrite
fi

if [ $STAGE -le 6 ]; then
    echo "Stage 6: Convert results to tables"
    # all
    python results_to_csv_cli.py --experiment_name "$EXP_NAME" --config_path config/city_conf_czechia.json config/city_conf_europe.json --log_level $LOGLEVEL
    # only CZ
    python results_to_csv_cli.py --experiment_name "$EXP_NAME" --config_path config/city_conf_czechia.json \
                                 --output_path "$EXP_NAME/Czechia" --log_level $LOGLEVEL
    # only Europe
    python results_to_csv_cli.py --experiment_name "$EXP_NAME" --config_path config/city_conf_europe.json \
                                 --output_path "$EXP_NAME/Europe" --log_level $LOGLEVEL
fi

if [ $STAGE -le 7 ]; then
    echo "Stage 7: Draw and save maps"
    python draw_maps_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_czechia.json" \
                            --output_path "$EXP_NAME/Czechia" --log_level $LOGLEVEL
    python draw_maps_cli.py --experiment_name "$EXP_NAME" --config_path "config/city_conf_europe.json" \
                            --output_path "$EXP_NAME/Europe" --log_level $LOGLEVEL
fi
