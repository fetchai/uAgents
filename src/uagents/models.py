import hashlib
from typing import Type, Union, Dict, ClassVar, Any

from pydantic import BaseModel
from pydantic.schema import model_schema, default_ref_template


class Model(BaseModel):
    schema_no_descriptions: ClassVar[Union[Dict[str, Any], None]] = None

    @staticmethod
    def _remove_descriptions(
        model: Type["Model"], orig_descriptions: Dict[str, Union[str, Dict]]
    ):
        for field_name, field in model.__fields__.items():
            if field.field_info and field.field_info.description:
                orig_descriptions[field_name] = field.field_info.description
                field.field_info.description = None
            elif issubclass(field.type_, Model):
                orig_descriptions[field_name] = {}
                Model._remove_descriptions(field.type_, orig_descriptions[field_name])

    @staticmethod
    def _restore_descriptions(
        model: Type["Model"], orig_descriptions: Dict[str, Union[str, Dict]]
    ):
        for field_name, field in model.__fields__.items():
            if (
                field.field_info
                and field_name in orig_descriptions
                and not issubclass(field.type_, Model)
            ):
                field.field_info.description = orig_descriptions[field_name]
            elif issubclass(field.type_, Model):
                Model._restore_descriptions(field.type_, orig_descriptions[field_name])

    @staticmethod
    def _refresh_schema_cache(model: Type["Model"]):
        schema = model_schema(model, by_alias=True, ref_template=default_ref_template)
        model.__schema_cache__[(True, default_ref_template)] = schema

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        type_obj = model if isinstance(model, type) else model.__class__
        if type_obj.schema_no_descriptions is None:
            orig_descriptions: Dict[str, Union[str, Dict]] = {}
            Model._remove_descriptions(type_obj, orig_descriptions)
        digest = (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )
        if type_obj.schema_no_descriptions is None:
            type_obj.schema_no_descriptions = type_obj.schema()
            Model._restore_descriptions(type_obj, orig_descriptions)
            Model._refresh_schema_cache(type_obj)
        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
