# Some definitions that should be hardcoded in the project for avoiding circular imports.
# We define the necessary constants here, and then import them into the corresponding module.
# In this meantime, avoid to import something from somewhere else here if it's not necessary.

import os

from .default import *
from .exceptions import *
from .info import *
from .path import *
from .version import *

Silian_ascii_art = r"""
           _              _   ____        _
     /\   | |            (_) |  _ \      | |
    /  \  | | ____ _ _ __ _  | |_) | ___ | |_
   / /\ \ | |/ / _` | '__| | |  _ < / _ \| __|
  / ____ \|   < (_| | |  | | | |_) | (_) | |_
 /_/    \_\_|\_\__,_|_|  |_| |____/ \___/ \__|
"""
Silian_config_filename = "config.toml"
Silian_dev_mode = str(os.getenv("DEV_MODE")).lower() == "true"
