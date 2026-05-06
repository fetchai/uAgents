import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _prepend_import_paths(project_root: Path) -> None:
    for p in (project_root, project_root / "src"):
        p_str = str(p)
        if p.exists() and p_str not in sys.path:
            sys.path.insert(0, p_str)


def _load_module_from_file(file_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _parse_graph_entry(graph_id: str, value: Any) -> tuple[str, str]:
    if isinstance(value, dict):
        if "path" not in value:
            raise RuntimeError(
                f"Invalid graph entry for '{graph_id}'. "
                "Expected a dict containing a 'path' key."
            )
        target = value["path"]
    elif isinstance(value, str):
        target = value
    else:
        raise RuntimeError(
            f"Invalid graph entry for '{graph_id}'. "
            "Expected either a string or a dict with a 'path' key."
        )

    if ":" not in target:
        raise RuntimeError(
            f"Invalid graph target '{target}' for graph '{graph_id}'. "
            "Expected format './path/to/file.py:variable' or 'my.module:variable'."
        )

    path_or_module, variable_name = target.rsplit(":", 1)
    return path_or_module, variable_name


def _extract_config_path(argv: list[str]) -> str:
    """Same default as ``langgraph dev`` (``--config`` defaults to ``langgraph.json``)."""
    for i, arg in enumerate(argv):
        if arg == "--config" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--config="):
            return arg.split("=", 1)[1]
    return "langgraph.json"


def _preload_graph_modules_from_config(config_path: str) -> None:
    """Import each graph module so module-level ``init()`` runs before LangGraph starts.

    Non-fatal: if the config is missing or malformed, we skip preloading and
    let the LangGraph CLI report the error with its own diagnostics.
    """
    config_file = Path(config_path).resolve()
    if not config_file.exists():
        return

    try:
        raw = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    graphs = raw.get("graphs", {})
    if not isinstance(graphs, dict) or not graphs:
        return

    project_root = config_file.parent

    _prepend_import_paths(project_root)

    file_modules: dict[Path, Any] = {}
    import_modules: dict[str, Any] = {}

    for graph_id, spec in graphs.items():
        try:
            path_or_module, variable_name = _parse_graph_entry(graph_id, spec)
        except RuntimeError:
            continue

        is_file = (
            "/" in path_or_module
            or path_or_module.endswith(".py")
            or path_or_module.startswith(".")
        )

        try:
            if is_file:
                file_path = (project_root / path_or_module).resolve()
                if not file_path.exists():
                    continue

                if file_path not in file_modules:
                    module_name = (
                        path_or_module.replace("/", "__")
                        .replace(".py", "")
                        .replace(" ", "_")
                        .lstrip(".")
                    ) or f"agentverse_user_graph_{graph_id}"
                    file_modules[file_path] = _load_module_from_file(
                        file_path, module_name
                    )

                module = file_modules[file_path]
            else:
                if path_or_module not in import_modules:
                    import_modules[path_or_module] = importlib.import_module(
                        path_or_module
                    )
                module = import_modules[path_or_module]
        except Exception:
            continue


def main() -> int:
    argv = sys.argv[1:]
    config_path = _extract_config_path(argv)
    _preload_graph_modules_from_config(config_path)

    from uagents_core.agentverse.sdk.langchain import agentverse_sdk

    sys.argv = [sys.argv[0], *argv]
    agentverse_sdk.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
