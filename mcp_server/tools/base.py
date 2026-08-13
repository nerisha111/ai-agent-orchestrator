from typing import Callable, Any, Type
from pydantic import BaseModel

class ToolMetadata:
    def __init__(self, name: str, description: str, input_model: Type[BaseModel], risk_level: str = "read"):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.risk_level = risk_level

def tool(name: str, description: str, input_model: Type[BaseModel], risk_level: str = "read"):
    def decorator(func: Callable[..., Any]):
        func._tool_metadata = ToolMetadata(
            name=name,
            description=description,
            input_model=input_model,
            risk_level=risk_level
        )
        return func
    return decorator
