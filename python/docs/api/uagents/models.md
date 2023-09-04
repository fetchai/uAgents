<a id="src.uagents.models"></a>

# src.uagents.models

<a id="src.uagents.models.Model"></a>

## Model Objects

```python
class Model(BaseModel)
```

Base class for all message models.

<a id="src.uagents.models.Model.build_schema_digest"></a>

#### build`_`schema`_`digest

```python
@staticmethod
def build_schema_digest(model: Union["Model", Type["Model"]]) -> str
```

Builds the schema digest for a given model.

