import copy
import hashlib
import json
from typing import Any, ClassVar

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

    @property
    def digest(self) -> str:
        """
        Property to access the digest of the protocol's manifest.

        Returns:
            str: The digest of the protocol's manifest.
        """
        return self.manifest()["metadata"]["digest"]

    def manifest(self, role: str | None = None) -> dict[str, Any]:
        """
        Generate the protocol's manifest, a long-form machine readable description of the
        protocol details and interface.

        Returns:
            dict[str, Any]: The protocol's manifest.
        """
        metadata = {
            "name": self.name,
            "version": self.version,
        }

        manifest = {
            "version": "1.0",
            "metadata": {},
            "models": [],
            "interactions": [],
        }

        if self.roles and role is not None:
            interactions = {
                model: replies
                for model, replies in self.interactions.items()
                if model in self.roles[role]
            }
        else:
            interactions = self.interactions

        all_models: dict[str, type[Model]] = {}
        all_replies: dict[str, dict[str, type[Model]]] = {}

        for model in interactions:
            model_digest = Model.build_schema_digest(model)
            all_models[model_digest] = model

        for model, replies in interactions.items():
            model_digest = Model.build_schema_digest(model)
            if len(replies) == 0:
                all_replies[model_digest] = {}
            else:
                for reply in replies:
                    reply_digest = Model.build_schema_digest(reply)
                    all_models[reply_digest] = reply
                    if model_digest in all_replies:
                        all_replies[model_digest][reply_digest] = reply
                    else:
                        all_replies[model_digest] = {reply_digest: reply}

        for schema_digest, model in all_models.items():
            manifest["models"].append(
                {"digest": schema_digest, "schema": model.schema()}
            )

        for request, responses in all_replies.items():
            manifest["interactions"].append(
                {
                    "type": "normal",
                    "request": request,
                    "responses": sorted(list(responses.keys())),
                }
            )

        encoded = json.dumps(manifest, indent=None, sort_keys=True).encode("utf8")
        metadata["digest"] = f"proto:{hashlib.sha256(encoded).digest().hex()}"

        final_manifest: dict[str, Any] = copy.deepcopy(manifest)
        final_manifest["metadata"] = metadata

        return final_manifest

    @staticmethod
    def manifest_raw(
        interactions: dict[type[Model], set[type[Model]]],
    ) -> dict[str, Any]:
        pass

    @staticmethod
    def compute_digest(manifest: dict[str, Any]) -> str:
        """
        Compute the digest of a given manifest.

        Args:
            manifest (dict[str, Any]): The manifest to compute the digest for.

        Returns:
            str: The computed digest.
        """
        cleaned_manifest = copy.deepcopy(manifest)
        if "metadata" in cleaned_manifest:
            del cleaned_manifest["metadata"]
        cleaned_manifest["metadata"] = {}

        encoded: bytes = json.dumps(
            obj=cleaned_manifest, indent=None, sort_keys=True
        ).encode("utf8")
        return f"proto:{hashlib.sha256(encoded).digest().hex()}"


def is_valid_protocol_digest(digest: str) -> bool:
    """
    Check if the given string is a valid protocol digest.

    Args:
        digest (str): The digest to be checked.

    Returns:
        bool: True if the digest is valid; False otherwise.
    """
    return len(digest) == 70 and digest.startswith("proto:")
