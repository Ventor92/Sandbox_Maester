from pydantic import BaseModel, root_validator
from typing import Any, Dict, Optional


class EventModel(BaseModel):
    type: str
    event: Dict[str, Any]

    @root_validator(pre=True)
    def check_type(cls, values):
        if values.get("type") != "event":
            raise ValueError("type must be 'event'")
        if not isinstance(values.get("event"), dict):
            raise ValueError("event must be an object")
        return values


class CustomEventModel(BaseModel):
    type: str
    event: Dict[str, Any]

    @root_validator(pre=True)
    def check_type(cls, values):
        if values.get("type") != "custom_event":
            raise ValueError("type must be 'custom_event'")
        if not isinstance(values.get("event"), dict):
            raise ValueError("event must be an object")
        return values


class RollModel(BaseModel):
    type: str
    expr: str
    intent: Optional[str] = ""

    @root_validator(pre=True)
    def check_type(cls, values):
        if values.get("type") != "roll":
            raise ValueError("type must be 'roll'")
        if not isinstance(values.get("expr"), str):
            raise ValueError("expr must be a string")
        return values
