import hashlib
from typing import Type, Union, Dict, ClassVar, Any

from pydantic import BaseModel
from pydantic.schema import model_schema, default_ref_template


class Model(BaseModel):
    schema_no_descriptions: ClassVar[Union[Dict[str, Any], None]] = None

    @classmethod
    def _remove_descriptions(
        cls, orig_descriptions: Dict[str, Union[str, Dict]]
    ):
        for field_name, field in cls.__fields__.items():
            if field.field_info and field.field_info.description:
                orig_descriptions[field_name] = field.field_info.description
                field.field_info.description = None
            elif issubclass(field.type_, Model):
                orig_descriptions[field_name] = {}
                Model._remove_descriptions(field.type_, orig_descriptions[field_name])

    @classmethod
    def _restore_descriptions(cls, orig_descriptions: Dict[str, Union[str, Dict]]
    ):
        for field_name, field in cls.__fields__.items():
            if (
                field.field_info
                and field_name in orig_descriptions
                and not issubclass(field.type_, Model)
            ):
                field.field_info.description = orig_descriptions[field_name]
            elif issubclass(field.type_, Model):
                Model._restore_descriptions(field.type_, orig_descriptions[field_name])

    @classmethod
    def _restore_schema_cache(cls):
        schema = model_schema(cls, by_alias=True, ref_template=default_ref_template)
        cls.__schema_cache__[(True, default_ref_template)] = schema

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        type_obj: Type["Model"] = model if isinstance(model, type) else model.__class__
        if type_obj.schema_no_descriptions is None:
            orig_descriptions: Dict[str, Union[str, Dict]] = {}
            type_obj._remove_descriptions(orig_descriptions)
        digest = (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )
        if type_obj.schema_no_descriptions is None:
            type_obj.schema_no_descriptions = type_obj.schema()
            type_obj._restore_descriptions(orig_descriptions)
            type_obj._restore_schema_cache()
        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
