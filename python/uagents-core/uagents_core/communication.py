from random import Random
from typing import Any

from uagents_core.config import AGENT_ADDRESS_LENGTH, AGENT_PREFIX
from uagents_core.crypto import is_user_address


def weighted_random_sample(
    items: list[Any],
    weights: list[float] | None = None,
    k: int = 1,
    rng: Random | None = None,
) -> list[Any]:
    """
    Weighted random sample from a list of items without replacement.

    Ref: Efraimidis, Pavlos S. "Weighted random sampling over data streams."

    Args:
        items (list[Any]): The list of items to sample from.
        weights (list[float]] | None) The optional list of weights for each item.
        k (int): The number of items to sample.
        rng (Random): The random number generator.

    Returns:
        list[Any]: The sampled items.
    """
    rng = rng or Random()
    if weights is None:
        return rng.sample(items, k=k)
    values: list[Any] = [rng.random() ** (1 / w) for w in weights]
    order: list[int] = sorted(range(len(items)), key=lambda i: values[i])
    return [items[i] for i in order[-k:]]


def is_valid_address(address: str) -> bool:
    """
    Check if the given string is a valid address.

    Args:
        address (str): The address to be checked.

    Returns:
        bool: True if the address is valid; False otherwise.
    """
    return is_user_address(address) or (
        len(address) == AGENT_ADDRESS_LENGTH and address.startswith(AGENT_PREFIX)
    )


def parse_identifier(identifier: str) -> tuple[str, str, str]:
    """
    Parse an agent identifier string into prefix, name, and address.

    Args:
        identifier (str): The identifier string to be parsed.

    Returns:
        tuple[str, str, str]: A Tuple containing the prefix, name, and address as strings.
    """
    prefix = ""
    name = ""
    address = ""

    if "://" in identifier:
        prefix, identifier = identifier.split("://", 1)

    if "/" in identifier:
        name, identifier = identifier.split("/", 1)

    if is_valid_address(identifier):
        address = identifier
    else:
        name = identifier

    return prefix, name, address
