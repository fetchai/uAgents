import importlib
import inspect
import json
import os


def get_classes_and_functions(module_name) -> list[tuple[str, str]]:
    members: list = []
    for member in inspect.getmembers(
        object=importlib.import_module(module_name, package=None),
    ):
        if inspect.isclass(member[1]) and member[1].__module__ == module_name:
            print(f"class: {member[0]}")
            members.append(f"class: {member[0]}")
        if inspect.isfunction(member[1]) and member[1].__module__ == module_name:
            print(f"function: {member[0]}")
            members.append(f"function: {member[0]}")
    return members


def get_modules(folder: str = ".") -> list[str]:
    modules: list[str] = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                cur_path = (
                    os.path.join(root, file)[:-3].split(folder)[1].replace("/", ".")
                )
                modules.append(cur_path[1:])
    return modules


def main(folder: str = ".") -> None:
    mods: list[str] = get_modules(folder)

    out = {}
    for mod in mods:
        print(f"Checking {mod}...")
        try:
            out[mod] = get_classes_and_functions(mod)
        except Exception:
            print("could not inspect module")
            continue
        print("")

    with open(file="list.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(out))


if __name__ == "__main__":
    main(os.path.join(os.getcwd(), "src"))
