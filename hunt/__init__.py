if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

from mods_base import Game, build_mod

from .drops import drop_hook, itemcard_hook, world_change_hook
from .mod_class import HuntTracker

__version__: str
__version_info__: tuple[int, ...]

build_mod(
    cls=HuntTracker,
    supported_games=Game.BL3,
    hooks=[drop_hook, itemcard_hook, world_change_hook],
)
