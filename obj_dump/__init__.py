if True:
    assert __import__("mods_base").__version_info__ >= (1, 0), "Please update the SDK"

from argparse import Namespace
from typing import Any, TextIO

import unrealsdk
from mods_base import build_mod, command
from unrealsdk.unreal import UObject, WrappedArray

__version__: str
__version_info__: tuple[int, ...]


def dump_object(obj: UObject, file: TextIO | None = None) -> None:
    """
    Dumps an object.

    Args:
        obj: The object to dump.
        file: An optional file to write to, instead of console.
    """
    print(f"==== Dump for object {obj} ====", file=file)
    for prop in obj.Class._properties():
        try:
            val = obj._get_field(prop)

            if isinstance(val, WrappedArray):
                arr: WrappedArray[Any] = val
                if len(arr) == 0:
                    print(f"{prop.Name}: []", file=file)
                    continue

                for idx, entry in enumerate(arr):
                    print(f"{prop.Name}[{idx}]: {entry!r}", file=file)
                continue

            print(f"{prop.Name}: {val!r}", file=file)
        except Exception:  # noqa: BLE001
            print(f"{prop.Name}: <unknown {prop.Class.Name}>", file=file)


@command(splitter=lambda line: [line.strip()])
def obj_dump(args: Namespace) -> None:  # noqa: D103
    dump_object(unrealsdk.find_object("Object", args.obj))


obj_dump.add_argument("obj", help="The object to dump. Should not include class.")

build_mod()
