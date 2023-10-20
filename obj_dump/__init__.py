if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

from argparse import Namespace
from typing import Any

import unrealsdk
from mods_base import Library, build_mod, command
from unrealsdk.unreal import WrappedArray

__version__: str
__version_info__: tuple[int, ...]


@command(splitter=lambda line: [line.strip()])
def obj_dump(args: Namespace) -> None:  # noqa: D103
    obj = unrealsdk.find_object("Object", args.obj)

    print(f"==== Dump for object {obj} ====")
    for prop in obj.Class._properties():
        try:
            val = obj._get_field(prop)

            if isinstance(val, WrappedArray):
                arr: WrappedArray[Any] = val
                if len(arr) == 0:
                    print(f"{prop.Name}: []")
                    continue

                for idx, entry in enumerate(arr):
                    print(f"{prop.Name}[{idx}]: {entry!r}")
                continue

            print(f"{prop.Name}: {val!r}")
        except Exception:  # noqa: BLE001
            print(f"{prop.Name}: <unknown {prop.Class.Name}>")


obj_dump.add_argument("obj", help="The object to dump. Should not include class.")

build_mod(cls=Library)
