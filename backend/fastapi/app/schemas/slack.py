from pydantic import BaseModel


class SlackConnectResponse(BaseModel):
    connect_url: str


class SlackChannelSelectionRequest(BaseModel):
    channel_id: str
    channel_name: str
