from random import Random
from typing import Any


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
