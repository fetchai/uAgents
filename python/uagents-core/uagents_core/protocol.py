from typing import ClassVar

from pydantic import BaseModel, ValidationInfo, field_validator

from uagents_core.models import Model


class ProtocolSpecification(BaseModel):
    """Specification for the interactions and roles of a protocol."""

    interactions: dict[type[Model], set[type[Model]]]
    roles: dict[str, set[type[Model]]] | None = None
    name: str = ""
    version: str = "0.1.0"

    SPEC_VERSION: ClassVar = "1.0"

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, roles, info: ValidationInfo):
        """
        Ensure that all models included in roles are also included in the interactions.
        """
        if roles is None:
            return roles

        interactions: dict[type[Model], set[type[Model]]] = info.data["interactions"]
        interaction_models = set(interactions.keys())

        for role, models in roles.items():
            invalid_models = models - interaction_models
            if invalid_models:
                model_names = [model.__name__ for model in invalid_models]
                raise ValueError(
                    f"Role '{role}' contains models that don't "
                    f"exist in interactions: {model_names}"
                )
        return roles


def is_valid_protocol_digest(digest: str) -> bool:
    """
    Check if the given string is a valid protocol digest.

    Args:
        digest (str): The digest to be checked.

    Returns:
        bool: True if the digest is valid; False otherwise.
    """
    return len(digest) == 70 and digest.startswith("proto:")
