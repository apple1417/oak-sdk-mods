from collections.abc import Callable

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

def close_db() -> None:
    """
    Closes the db connection, to allow the file to be replaced.

    Note the connection will be re-opened the next time it's required.
    """
