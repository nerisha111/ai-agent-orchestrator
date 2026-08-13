#to prove that the registry auto-discovery functions correctly

from pydantic import BaseModel, Field
from tools.base import tool

class EchoInput(BaseModel):
    message: str = Field(..., description="The string to be echoed back to verify communication")

@tool(
    name="echo_test",
    description="accepts a message and returns it back to verify end to end communication",
    input_model=EchoInput,
    risk_level="read"
)
def echo_test(message: str) -> dict:
    return {
        "status": "success",
        "echo" : message
    }