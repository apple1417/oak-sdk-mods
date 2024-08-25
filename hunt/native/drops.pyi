from collections.abc import Callable

from unrealsdk.unreal import UObject

InventoryBalanceStateComponent = UObject

def set_db_getter(getter: Callable[[], str]) -> Callable[[], str]:
    """
    Sets the function used to get the db path.

    This function takes no args, should ensure the db file exists, and return the
    path to it.

    Args:
        getter: The getter function to set.
    Returns:
        The passed getter, so that this may be used as a decorator.
    """

def set_drop_callback(callback: Callable[[str], None]) -> Callable[[str], None]:
    """
    Sets the callback run when a valid drop is collected.

    This callback takes a single arg, the balance name of the item which was
    collected. The return value is ignored.

    Args:
        callback: The callback to set.
    Returns:
        The passed callback, so that this may be used as a decorator.
    """

def set_coop_blink_count(num_blinks: int) -> None:
    """
    Sets the number of times items will blink during coop transmission.

    Set to 0 to disable coop support.

    Args:
        num_blinks: The number of times to blink.
    """

def close_db() -> None:
    """
    Closes the db connection, to allow the file to be replaced.

    Note the connection will be re-opened the next time it's required.
    """

def get_inventory_balance_name(bal_comp: InventoryBalanceStateComponent) -> str:
    """
    Gets the name of this item's inventory balance.

    Args:
        bal_comp: The InventoryBalanceStateComponent to inspect.
    Return:
        The inventory balance's name.
    """

def enable() -> None:
    """Enables the drop detection hooks."""

def disable() -> None:
    """Disables the drop detection hooks."""
