import requests
import yaml
import json
import os
from urllib.parse import urljoin
import logging
import argparse
from datetime import datetime

logger = logging.getLogger("app")


class ConfigError(Exception):
    pass


def read_config(config_path, app):
    with open(config_path, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    try:
        app_config = config[app]
        logger.debug(f"Loaded config: {app_config}")
        return app_config
    except KeyError:
        raise ConfigError(
            f"There is no app config: {app}. "
            f"Existing options: {list(config.keys())}")


def get_auth_token(config):
    resp = requests.post(urljoin(config["url"], config["auth"]["end_point"]),
                         json=config["auth"]["payload"],
                         timeout=10)
    resp.raise_for_status()
    auth_token = f"JWT {resp.json()['access_token']}"
    return auth_token


def get_out_of_stock(config, dates):
    data = {}
    for date in dates:
        resp = requests.get(
            urljoin(config["url"], config["out_of_stock"]["end_point"]),
            headers={"Authorization": get_auth_token(config)},
            json={"date": date},
            timeout=10)
        resp.raise_for_status()
        data[date] = json.loads(resp.content)
    return data


def make_data_dir(date):
    data_dir = os.path.join("data", date)
    try:
        os.makedirs(data_dir, exist_ok=False)
    except OSError:
        logger.warning(f"{data_dir} already exists, overriding.")
    return data_dir


def _set_logger(verbose):
    logging.basicConfig()
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)


def store_data_for_the_date(date, out_of_stock):
    data_dir = make_data_dir(date)
    json_file_path = os.path.join(data_dir, "out_of_stock.json")
    with open(json_file_path, "w") as json_file:
        json.dump(out_of_stock, json_file)
    logger.info(f"Successfully stored response to {json_file_path}")


def store_out_of_stock(config_path, app, dates, verbose=False):
    _set_logger(verbose)

    config = read_config(config_path, app=app)
    out_of_stock_data = get_out_of_stock(
        config, dates)
    for date, out_of_stock in out_of_stock_data.items():
        store_data_for_the_date(date, out_of_stock)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config.yml")
    parser.add_argument("--dates", type=str, nargs="+",
                        default=["2021-01-01"])
    parser.add_argument("--app", type=str, default="app")
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()
    print(args)
    store_out_of_stock(
        config_path=args.config_path,
        app=args.app,
        dates=args.dates,
        verbose=args.verbose)
