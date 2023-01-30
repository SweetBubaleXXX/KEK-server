from api import config


def setup_config():
    config.settings = config.Settings(_env_file=".config.test")
    return config.settings
