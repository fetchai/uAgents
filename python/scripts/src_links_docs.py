import importlib
import inspect
import os
import pkgutil
import re

import uagents


def extract_classes_and_methods(library_name):
    results = []

    for _, modname, _ in pkgutil.walk_packages(
        library_name.__path__, library_name.__name__ + "."
    ):
        try:
            module = importlib.import_module(modname)
        except ImportError:
            continue

        for name, obj in inspect.getmembers(module):
            try:
                if (
                    "uagents" in obj.__module__
                    and modname in f"{obj.__module__}.{obj.__name__}"
                ):
                    module_info = {
                        "module": modname,
                        "class_name": name if inspect.isclass(obj) else "module.func",
                        "import_path": f"{obj.__module__}.{obj.__name__}",
                        "source_line": inspect.getsourcelines(obj)[-1],
                        "methods": [],
                        "properties": [],
                        "setters": [],
                        "module_functions": [],
                    }

                    if inspect.isclass(obj) and obj.__module__ == modname:
                        for method_name, method in inspect.getmembers(
                            obj, predicate=inspect.isfunction
                        ):
                            try:
                                method_info = {
                                    "method_name": method_name,
                                    "is_classmethod": inspect.ismethod(method),
                                    "source_line": inspect.getsourcelines(method)[-1]
                                    if inspect.isfunction(method)
                                    else None,
                                }
                                module_info["methods"].append(method_info)
                            except Exception as e:
                                print(f"Error processing setter for {method_name}: {e}")

                        for attr_name, attr_value in inspect.getmembers(obj):
                            if isinstance(attr_value, property):
                                try:
                                    prop_info = {
                                        "property_name": attr_name,
                                        "docstring": attr_value.__doc__,
                                        "source_line": inspect.getsourcelines(
                                            attr_value.fget
                                        )[-1]
                                        if attr_value.fget
                                        else None,
                                    }
                                    module_info["properties"].append(prop_info)
                                except Exception as e:
                                    print(
                                        f"Error processing setter for {attr_name}: {e}"
                                    )

                                if attr_value.fset:
                                    try:
                                        setter_info = {
                                            "setter_name": f"{attr_name}.setter",
                                            "docstring": attr_value.fset.__doc__,
                                            "source_line": inspect.getsourcelines(
                                                attr_value.fset
                                            )[-1],
                                        }
                                        module_info["setters"].append(setter_info)
                                    except Exception as e:
                                        print(
                                            f"Error processing setter for {attr_name}: {e}"
                                        )

                    elif inspect.isfunction(obj):
                        # this is finding function of the module, but not function of the obj.

                        mlf = {
                            "module_function": obj.__name__,
                            "docstring": obj.__doc__,
                            "source_line": inspect.getsourcelines(obj)[-1],
                        }
                        module_info["module_functions"].append(mlf)

                    results.append(module_info)
            except Exception as _:
                pass

    return results


def update_markdown(md_file_path, classes_data):
    markdown_link_pattern = r"\[[^\]]*?\]\([^\)]*?\)"
    with open(md_file_path, "r") as file:
        content = file.read()

    updated_content = content
    for cls_data in classes_data:
        class_name = cls_data["class_name"]
        methods = cls_data["methods"]
        module_functions = cls_data["module_functions"]
        properties = cls_data["properties"]
        setters = cls_data["setters"]
        source_line = cls_data["source_line"]
        class_header_pattern = rf"(## {re.escape(class_name)}\s.*?\n)"
        class_match = re.search(class_header_pattern, updated_content, re.DOTALL)

        parts = md_file_path.split("/")
        code_filepath = (
            "/".join(parts[len(parts) - 2 :])
            .replace('"', "")
            .replace(".md", ".py")
            .replace("uagents/", "")
        )

        # probably a module function or var
        if not class_match:
            for func in module_functions:
                func_name = func["module_function"]
                source_line = func["source_line"]

                func_header_pattern = rf"(#### {func_name}\s.*?\n)"
                func_match = re.search(func_header_pattern, updated_content, re.DOTALL)

                if func_match:
                    func_start_index = func_match.end()
                    func_start = func_start_index

                    updated_content = (
                        updated_content[:func_start].rstrip()
                        + f"[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/{code_filepath}#L{source_line})\n"
                        + updated_content[func_start:]
                    )

                else:
                    print(f"no match , {class_name}, {func_match}", func_name)

        else:
            start_index = class_match.end()

            if class_match.group(1).rstrip().endswith(")"):
                updated_content = re.sub(markdown_link_pattern, "", updated_content)

            updated_content = (
                updated_content[:start_index].rstrip()
                + f"[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/{code_filepath}#L{source_line})\n"
                + updated_content[start_index:]
            )

            for method in methods:
                method_name = method["method_name"]
                source_line = method["source_line"]
                method_header_pattern = rf"(#### {method_name}\s.*?\n)"
                method_match = re.search(
                    method_header_pattern, updated_content[start_index:], re.DOTALL
                )

                if method_match:
                    method_start_index = method_match.end()
                    method_start = start_index + method_start_index

                    updated_content = (
                        updated_content[:method_start].rstrip()
                        + f"[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/{code_filepath}#L{source_line})\n"
                        + updated_content[method_start:]
                    )

                else:
                    print(f"no match, {class_name}, {method_match}", method_name)

            for property in properties:
                property_name = property["property_name"]
                source_line = property["source_line"]

                property_header_pattern = rf"(#### {property_name}\s.*?\n)"
                property_match = re.search(
                    property_header_pattern, updated_content[start_index:], re.DOTALL
                )

                if property_match:
                    property_start_index = property_match.end()
                    property_start = start_index + property_start_index

                    updated_content = (
                        updated_content[:property_start].rstrip()
                        + f"[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/{code_filepath}#L{source_line})\n"
                        + updated_content[property_start:]
                    )

                else:
                    print(f"no match, {class_name}, {property_match}", property_name)

            for setter in setters:
                setter_name = setter["setter_name"]
                source_line = setter["source_line"]
                setter_header_pattern = rf"(#### {setter_name}\s.*?\n)"
                setter_match = re.search(
                    setter_header_pattern, updated_content[start_index:], re.DOTALL
                )

                if setter_match:
                    setter_start_index = setter_match.end()
                    setter_start = start_index + setter_start_index

                    updated_content = (
                        updated_content[:setter_start].rstrip()
                        + f"[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/{code_filepath}#L{source_line})\n"
                        + updated_content[setter_start:]
                    )

                else:
                    print(f"no match, {class_name}, {setter_match}", setter_name)
    with open(md_file_path, "w") as file:
        file.write(updated_content)


data = extract_classes_and_methods(uagents)

directory_path = "../docs/api/uagents/"


def update_mds(directory=directory_path):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                update_markdown(file_path, data)


update_mds(directory_path)
