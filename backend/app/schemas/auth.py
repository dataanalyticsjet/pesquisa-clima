from pydantic import BaseModel, ConfigDict


class AuthenticatedUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    email: str
    access_type: str
    roles: list[str]


class AuthMeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authenticated: bool
    user: AuthenticatedUserResponse


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authenticated: bool
