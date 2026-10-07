"""Generated operation contract shared by the HTTP and AI adapters."""

from copy import deepcopy

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import ResolvedComponent
from rest_framework import serializers

from dekopen_engine.design_operations import OPERATION_SCHEMA, OperationError, validate_operation


class DesignOperationSerializer(serializers.Serializer):
    def to_internal_value(self, value):
        try:
            return validate_operation(value)
        except OperationError as error:
            raise serializers.ValidationError(str(error)) from error

    def to_representation(self, value):
        return value


class DesignOperationSchema(OpenApiSerializerExtension):
    target_class = DesignOperationSerializer
    def map_serializer(self, auto_schema, direction):
        schema = deepcopy(OPERATION_SCHEMA)
        if direction != "request":
            for item in schema["oneOf"]:
                item["properties"].update(base_sig={"type": "string"}, description={"type": "string"}, result={"type": "object", "additionalProperties": True}, context_effect={"type": "object", "additionalProperties": {"type": "string"}})
        def nullable(value):
            if isinstance(value, dict):
                if isinstance(value.get("type"), list):
                    types = value["type"]
                    value["type"] = next(kind for kind in types if kind != "null")
                    value["nullable"] = "null" in types
                return {key: nullable(child) for key, child in value.items()}
            if isinstance(value, list):
                return [nullable(child) for child in value]
            return value
        schema = nullable(schema)
        references = []
        mapping = {}
        for definition in schema["oneOf"]:
            name = definition["properties"]["op"]["enum"][0]
            component_name = "Operation" + "".join(word.title() for word in name.split("_")) + ("Request" if direction == "request" else "")
            component = ResolvedComponent(name=component_name, type=ResolvedComponent.SCHEMA,
                                          object=(name, direction), schema=definition)
            auto_schema.registry.register_on_missing(component)
            references.append(component.ref)
            mapping[name] = component.ref["$ref"]
        return {"oneOf": references, "discriminator": {"propertyName": "op", "mapping": mapping}}


