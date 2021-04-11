import requests
import yaml
import json
import os
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    pass

def read_config(config_path, app="app"):
    with open(config_path, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    try:
        app_config = config[app]
        logger.debug(f"Loaded config: {app_config}")
        return app_config
    except KeyError:
        raise ConfigError(f"There is no app config: {app}. Existing options: {list(config.keys())}")

def get_auth_token(config):
    resp = requests.post(urljoin(config["url"], config["auth"]["end_point"]), 
                         json=config["auth"]["payload"])
    resp.raise_for_status()
    auth_token = f"JWT {resp.json()['access_token']}"
    return auth_token

def get_out_of_stock(config):
    resp = requests.get(urljoin(config["url"], config["out_of_stock"]["end_point"]),
                        headers={"Authorization": get_auth_token(config)},
                        json=config["out_of_stock"]["payload"])
    resp.raise_for_status()
    return json.loads(resp.content)

def make_data_dir(date):
    data_dir = os.path.join("data", date)
    try:
        os.makedirs(data_dir, exist_ok=False)
    except OSError:
        logger.warning(f"{data_dir} already exists")
    return data_dir

def _set_logger(verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

def store_out_of_stock(config_path, app="app", verbose=False):
    _set_logger(verbose)

    config = read_config(config_path, app=app)
    resp = get_out_of_stock(config)
    data_dir = make_data_dir(config['out_of_stock']['payload']['date'])

    with open(os.path.join(data_dir, "out_of_stock.json"), "w") as json_file:
        json.dump(resp, json_file)
        
if __name__ == "__main__":
    import fire
    fire.Fire(store_out_of_stock)

# store_out_of_stock("config.yml", verbose=1)
