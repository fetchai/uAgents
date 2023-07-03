import hashlib
from typing import Type, Union, Dict

from pydantic import BaseModel
from pydantic.schema import model_schema, default_ref_template
from pydantic.main import BaseModel

class Model(BaseModel):
    @staticmethod
    def _remove_descriptions(model: Union["Model", Type["Model"]], orig_descriptions: Dict[str, Union[str, Dict]]):
        for _, field in model.__fields__.items():
            if field.field_info and field.field_info.description:
                orig_descriptions[field.name] = field.field_info.description
                field.field_info.description = None
            elif issubclass(field.type_, Model):
                orig_descriptions[field.name] = {}
                Model._remove_descriptions(field.type_, orig_descriptions[field.name])

    @staticmethod
    def _restore_descriptions(model: Union["Model", Type["Model"]], orig_descriptions: Dict[str, Union[str, Dict]]):
        for _, field in model.__fields__.items():
            if field.field_info and field.name in orig_descriptions and not issubclass(field.type_, Model):
                field.field_info.description = orig_descriptions[field.name]
            elif issubclass(field.type_, Model):
                Model._restore_descriptions(field.type_, orig_descriptions[field.name])

    @staticmethod
    def _refresh_schema_cache(model: Union["Model", Type["Model"]], by_alias: bool = True, ref_template: str = default_ref_template):
        s = model_schema(model, by_alias, ref_template)
        model.__schema_cache__[(True, default_ref_template)] = s

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        orig_descriptions: Dict[str, Union[str, Dict]] = {}
        Model._remove_descriptions(model, orig_descriptions)
        digest = (
            hashlib.sha256(
                model.schema_json(indent=None, sort_keys=True).encode("utf8")
            )
            .digest()
            .hex()
        )
        Model._restore_descriptions(model, orig_descriptions)
        Model._refresh_schema_cache(model)
        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
