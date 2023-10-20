# ruff: noqa: D103
if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

import unrealsdk
from mods_base import Library, build_mod, keybind

__version__: str
__version_info__: tuple[int, ...]


@keybind("Skip Dialog")
def skip_dialog() -> None:
    for dialog in unrealsdk.find_all("GbxDialogComponent", exact=False):
        thread_id = dialog.CurrentPerformance.DialogThreadID
        if thread_id > 0:
            dialog.StopPerformance(thread_id, True)


build_mod(cls=Library)
