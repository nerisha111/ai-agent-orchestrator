# Handles runtime file-system walks under tools/
# Imports discovered modules and exposes them
# Guarantees that the core orchestrator remains completely
# decoupled from individual business capabilities

import os
import importlib
import inspect
from typing import Dict, Any, Callable, List

from tools.base import ToolMetadata


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable[..., Any]] = {}

    def discover_tools(self, tools_dir: str = "tools"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(current_dir, tools_dir)

        if not os.path.exists(target_dir):
            return

        for filename in os.listdir(target_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module_name = f"tools.{module_name}"

                try:
                    module = importlib.import_module(full_module_name)
                    importlib.reload(module)

                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj) and hasattr(
                            obj, "_tool_metadata"
                        ):
                            meta: ToolMetadata = obj._tool_metadata
                            self.tools[meta.name] = obj

                except Exception as e:
                    print(
                        f"Error loading tool module "
                        f"{full_module_name}: {e}"
                    )

    def get_tool_metadata(self, name: str) -> ToolMetadata:
        func = self.tools.get(name)

        if func and hasattr(func, "_tool_metadata"):
            return func._tool_metadata

        raise ValueError(
            f"Tool '{name}' was not found in the registry."
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        tool_list = []

        for name, func in self.tools.items():
            meta: ToolMetadata = func._tool_metadata

            tool_list.append({
                "name": meta.name,
                "description": meta.description,
                "risk_level": meta.risk_level,
                "schema": meta.input_model.model_json_schema()
            })

        return tool_list


registry = ToolRegistry()