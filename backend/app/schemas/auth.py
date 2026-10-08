from pydantic import BaseModel, ConfigDict, Field


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


class ExternalCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)


class ExternalCodeVerifyRequest(ExternalCodeRequest):
    code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")


class ExternalCodeRequestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str


class ExternalCodeVerifyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authenticated: bool
