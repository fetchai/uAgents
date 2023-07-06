import hashlib
from typing import Type, Union, Dict, Any
import json
import copy
from pydantic import BaseModel


class Model(BaseModel):
    _schema_no_descriptions = None

    @staticmethod
    def remove_descriptions(schema: Dict[str, Dict[str, str]]):
        if not "properties" in schema:
            return

        fields_with_descr = []
        for field_name, field_props in schema["properties"].items():
            if "description" in field_props:
                fields_with_descr.append(field_name)
        for field_name in fields_with_descr:
            del schema["properties"][field_name]["description"]

        if "definitions" in schema:
            for definition in schema["definitions"].values():
                Model.remove_descriptions(definition)

    @classmethod
    def schema_no_descriptions(cls) -> Dict[str, Any]:
        if cls._schema_no_descriptions is None:
            schema = copy.deepcopy(cls.schema())
            Model.remove_descriptions(schema)
            cls._schema_no_descriptions = schema
        return cls._schema_no_descriptions

    @classmethod
    def schema_json_no_descriptions(cls) -> str:
        return json.dumps(cls.schema_no_descriptions(), indent=None, sort_keys=True)

    @staticmethod
    def build_schema_digest(model: Union["Model", Type["Model"]]) -> str:
        digest = (
            hashlib.sha256(model.schema_json_no_descriptions().encode("utf-8"))
            .digest()
            .hex()
        )
        return f"model:{digest}"


class ErrorMessage(Model):
    error: str
