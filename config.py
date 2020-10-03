import os
import atexit
from configparser import ConfigParser

home = os.environ['HOME']
cfgpath = os.path.join(home, '.yated.ini')
cfg = ConfigParser()
cfg.read(cfgpath)
if 'config' not in cfg:
    cfg['config'] = {}
section = cfg['config']


def get(name, default=''):
    if name not in section:
        section[name] = default
    return section.get(name)


def getint(name, default=0):
    return int(get(name, str(default)))


def getbool(name, default=False):
    return get(name, str(default)) != 'False'


def set(name, value):
    section[name] = str(value)


def save_cfg():
    with open(cfgpath, 'w') as configfile:
        cfg.write(configfile)


atexit.register(save_cfg)
