from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    name: str | None = None
    picture: str | None = None
    receive_updates: bool | None = None
