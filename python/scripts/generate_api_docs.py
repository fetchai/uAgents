"""This tool generates the API docs."""

import importlib
import inspect
import pkgutil
import re
import shutil
import subprocess
from pathlib import Path

import uagents

DOCS_DIR = Path("docs/")
API_DIR = DOCS_DIR / "api/"
UAGENTS_DIR = Path("src/uagents")

IGNORE_NAMES = {}
IGNORE_PREFIXES = {
    Path(UAGENTS_DIR, "__init__.py"),
    Path(UAGENTS_DIR, "contrib"),
}

MARKDOWN_LINK_PATTERN = r"\[[^\]]*?\]\([^\)]*?\)"


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
            except Exception as _:  # pylint: disable=broad-except
                pass

    return results


def create_subdir(path: str) -> None:
    """
    Create a subdirectory.

    Args:
        path (str): The directory path
    """
    directory = "/".join(path.split("/")[:-1])
    Path(directory).mkdir(parents=True, exist_ok=True)


def replace_underscores(text: str) -> str:
    """
    Replace escaped underscores in text.

    Args:
        text (str): The text to replace underscores in

    Returns:
        str: The processed text
    """
    text_a = text.replace("\\_\\_", "`__`")
    text_b = text_a.replace("\\_", "`_`")
    return text_b


def is_relative_to(path_1: Path, path_2: Path) -> bool:
    """Check if a path is relative to another path."""
    return str(path_1).startswith(str(path_2))


def is_not_dir(path: Path) -> bool:
    """Call p.is_dir() method and negate the result."""
    return not path.is_dir()


def should_skip(module_path: Path) -> bool:
    """Return true if the file should be skipped."""
    if any(re.search(pattern, module_path.name) for pattern in IGNORE_NAMES):
        print("Skipping, it's in ignore patterns")
        return True
    if module_path.suffix != ".py":
        print("Skipping, it's not a Python module.")
        return True
    if any(is_relative_to(module_path, prefix) for prefix in IGNORE_PREFIXES):
        print(f"Ignoring prefix {module_path}")
        return True
    return False


def generate_api_docs_uagents_modules(class_data) -> None:
    """Generate API docs for uagents.* modules."""
    for module_path in filter(is_not_dir, Path(UAGENTS_DIR).rglob("*")):
        print(f"Processing {module_path}... ", end="")
        if should_skip(module_path):
            continue
        parents = module_path.parts[:-1]
        parents_without_root = module_path.parts[1:-1]
        last = module_path.stem
        doc_file = API_DIR / Path(*parents_without_root) / f"{last}.md"
        dotted_path = ".".join(parents) + "." + last
        make_pydoc(dotted_path, doc_file)
        clean_headings_remove_links(doc_file)
        add_links_from_class_data(doc_file, class_data)


def make_pydoc(dotted_path: str, destination_file: Path) -> None:
    """Make a PyDoc file."""
    print(
        f"Running with dotted path={dotted_path} and destination_file={destination_file}... ",
        end="",
    )
    try:
        api_doc_content = run_pydoc_markdown(dotted_path)
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        destination_file.write_text(api_doc_content)
    except Exception as ex:  # pylint: disable=broad-except
        print(f"Error: {str(ex)}")
        return
    print("Done!")


def run_pydoc_markdown(module: str) -> str:
    """
    Run pydoc-markdown.

    Args:
        module (str): The dotted path.

    Returns:
        str: the PyDoc content (pre-processed).
    """
    with subprocess.Popen(
        ["pydoc-markdown", "-m", module, "-I", "."], stdout=subprocess.PIPE
    ) as pydoc:
        stdout, _ = pydoc.communicate()
        pydoc.wait()
        stdout_text = stdout.decode("utf-8")
        return replace_underscores(stdout_text)


def clean_headings_remove_links(file: Path):
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        header_match = re.match(r"^(#+)\s+(.*)", line)

        url_pattern = re.compile(r"<a id=\"(.*?)\">(.*?)</a>")
        sub_line = re.sub(url_pattern, "", line)

        if header_match:
            level = len(header_match.group(1))  # Number of `#` indicates header level
            header_text = header_match.group(2).strip()
            header_text = header_text.replace("`", "")
            # Reconstruct the header line
            updated_lines.append(f"{'#' * level} {header_text}\n")
        else:
            updated_lines.append(sub_line)

    # Write the updated content back to the file
    with open(file, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)


def add_links_from_class_data(markdown_file: Path, classes_data):
    with open(markdown_file, "r", encoding="utf-8") as file:
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

        parts = markdown_file.__str__().split("/")
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
                    print(f"no match, {class_name}, {func_match}", func_name)

        else:
            start_index = class_match.end()

            if class_match.group(1).rstrip().endswith(")"):
                updated_content = re.sub(MARKDOWN_LINK_PATTERN, "", updated_content)

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

            for prop in properties:
                property_name = prop["property_name"]
                source_line = prop["source_line"]

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
    with open(markdown_file, "w", encoding="utf-8") as file:
        file.write(updated_content)


if __name__ == "__main__":
    shutil.rmtree(API_DIR, ignore_errors=True)
    API_DIR.mkdir()
    generate_api_docs_uagents_modules(extract_classes_and_methods(uagents))
