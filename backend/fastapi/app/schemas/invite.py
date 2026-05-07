from pydantic import BaseModel


class InviteMemberRequest(BaseModel):
    email: str


class AcceptInviteRequest(BaseModel):
    token: str
    password: str