# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

# pylint: disable=protected-access

from typing import Callable, Mapping

from azure.ai.ml.dsl._dynamic import KwParameter, create_kw_function_from_parameters
from azure.ai.ml.entities import Component as ComponentEntity
from azure.ai.ml.entities._builders import Command


def get_dynamic_input_parameter(inputs: Mapping):
    """Return the dynamic parameter of the definition's input ports."""
    return [
        KwParameter(
            name=name,
            annotation=input._get_python_builtin_type_str(),
            default=None,
            _type=input._get_python_builtin_type_str(),
        )
        for name, input in inputs.items()
    ]


def to_component_func(entity: ComponentEntity, component_creation_func) -> Callable[..., Command]:
    func_name = "[component] {}".format(entity.display_name)

    func_docstring_lines = []
    if entity.description is not None:
        func_docstring_lines.append(entity.description.strip())

    all_params = get_dynamic_input_parameter(entity.inputs)

    flattened_group_keys = []
    # Flatten all group parameters, for function parameter validation.
    from azure.ai.ml.entities._inputs_outputs import GroupInput
    for name, item in entity.inputs.items():
        if isinstance(item, GroupInput):
            flattened_group_keys.extend(list(item.flatten(group_parameter_name=name).keys()))

    doc_string = entity.description
    # Try add yaml to doc string
    try:
        yaml_str = entity._yaml_str if entity._yaml_str else entity._to_yaml()
        doc_string = "{0}\n\nComponent yaml:\n```yaml\n{1}\n```".format(doc_string, yaml_str)
    except Exception:  # pylint: disable=broad-except
        pass

    dynamic_func = create_kw_function_from_parameters(
        component_creation_func,
        documentation=doc_string,
        parameters=all_params,
        func_name=func_name,
        flattened_group_keys=flattened_group_keys,
    )

    return dynamic_func
