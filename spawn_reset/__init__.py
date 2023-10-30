# ruff: noqa: D103
if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

import unrealsdk
from mods_base import build_mod, keybind
from ui_utils import show_hud_message

__version__: str
__version_info__: tuple[int, ...]


@keybind("Spawn Reset")
def reset_spawns() -> None:
    for spawner in unrealsdk.find_all("SpawnerComponent", exact=False):
        spawner.DestroyAllActors()
        spawner.ResetSpawning()
    show_hud_message("Spawn Resetter", ("Spawns Reset"))


build_mod()
