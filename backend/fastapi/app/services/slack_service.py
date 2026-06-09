from datetime import datetime, timedelta
import json
import logging
from typing import Any
from urllib.parse import urlencode

import jwt
import requests
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config.settings import (
    FRONTEND_URL,
    SECRET_KEY,
    SLACK_BOT_SCOPES,
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET,
    SLACK_REDIRECT_URI,
)
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.slack_channel import SlackChannel
from app.models.slack_workspace import SlackWorkspace
from app.models.tenant import Tenant
from app.models.user import User
from app.tasks.email_tasks import send_incident_alert_email_task


SLACK_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_ACCESS_URL = "https://slack.com/api/oauth.v2.access"
SLACK_CHANNELS_URL = "https://slack.com/api/conversations.list"
SLACK_CHANNEL_INFO_URL = "https://slack.com/api/conversations.info"
SLACK_CHANNEL_JOIN_URL = "https://slack.com/api/conversations.join"
SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"

logger = logging.getLogger(__name__)


def require_slack_configuration() -> None:
    missing = [
        name
        for name, value in (
            ("SLACK_CLIENT_ID", SLACK_CLIENT_ID),
            ("SLACK_CLIENT_SECRET", SLACK_CLIENT_SECRET),
            ("SLACK_REDIRECT_URI", SLACK_REDIRECT_URI),
        )
        if not value
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Slack is not configured. Missing: {', '.join(missing)}",
        )


def _clean_workspace_hint(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def _normalize_workspace_name(value: str | None) -> str:
    if not value:
        return ""
    return "".join(character.lower() for character in value if character.isalnum())


def build_oauth_state(
    *,
    tenant_id: str,
    user_id: str,
    expected_team_name: str | None = None,
    expected_team_id: str | None = None,
) -> str:
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "purpose": "slack_oauth",
        "exp": datetime.utcnow() + timedelta(minutes=15),
    }
    expected_team_name = _clean_workspace_hint(expected_team_name)
    expected_team_id = _clean_workspace_hint(expected_team_id)
    if expected_team_name:
        payload["expected_team_name"] = expected_team_name
    if expected_team_id:
        payload["expected_team_id"] = expected_team_id
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_oauth_state(state: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=400, detail="Slack connection expired. Please try again.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=400, detail="Invalid Slack OAuth state.") from exc

    if payload.get("purpose") != "slack_oauth":
        raise HTTPException(status_code=400, detail="Invalid Slack OAuth state.")

    return payload


def build_connect_url(
    *,
    tenant_id: str,
    user_id: str,
    expected_team_name: str | None = None,
    expected_team_id: str | None = None,
) -> str:
    require_slack_configuration()
    expected_team_name = _clean_workspace_hint(expected_team_name)
    expected_team_id = _clean_workspace_hint(expected_team_id)

    params = {
        "client_id": SLACK_CLIENT_ID,
        "scope": SLACK_BOT_SCOPES,
        "redirect_uri": SLACK_REDIRECT_URI,
        "state": build_oauth_state(
            tenant_id=tenant_id,
            user_id=user_id,
            expected_team_name=expected_team_name,
            expected_team_id=expected_team_id,
        ),
    }
    if expected_team_id:
        params["team"] = expected_team_id

    return f"{SLACK_AUTHORIZE_URL}?{urlencode(params)}"


def validate_expected_workspace(
    installation: dict[str, Any],
    *,
    expected_team_name: str | None,
    expected_team_id: str | None,
) -> None:
    team = installation.get("team") or {}
    actual_team_id = team.get("id")
    actual_team_name = team.get("name") or actual_team_id

    if expected_team_id and actual_team_id != expected_team_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Slack returned workspace {actual_team_id or 'unknown'}, but you requested "
                f"{expected_team_id}. Switch workspace in Slack and try again."
            ),
        )

    if (
        expected_team_name
        and _normalize_workspace_name(actual_team_name)
        != _normalize_workspace_name(expected_team_name)
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Slack returned workspace '{actual_team_name}', but you entered "
                f"'{expected_team_name}'. Choose the correct Slack workspace and try again."
            ),
        )


def build_connect_url_legacy(*, tenant_id: str, user_id: str) -> str:
    """Kept only for older callers while the UI migrates to explicit workspace selection."""
    require_slack_configuration()
    params = urlencode(
        {
            "client_id": SLACK_CLIENT_ID,
            "scope": SLACK_BOT_SCOPES,
            "redirect_uri": SLACK_REDIRECT_URI,
            "state": build_oauth_state(tenant_id=tenant_id, user_id=user_id),
        }
    )
    return f"{SLACK_AUTHORIZE_URL}?{params}"


def exchange_code_for_installation(code: str) -> dict[str, Any]:
    require_slack_configuration()

    response = requests.post(
        SLACK_ACCESS_URL,
        data={
            "code": code,
            "redirect_uri": SLACK_REDIRECT_URI,
        },
        auth=(SLACK_CLIENT_ID, SLACK_CLIENT_SECRET),
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    if not payload.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=f"Slack OAuth failed: {payload.get('error', 'unknown_error')}",
        )

    return payload


def upsert_workspace_installation(
    db: Session,
    *,
    tenant_id: str,
    connected_by_user_id: str,
    installation: dict[str, Any],
) -> SlackWorkspace:
    team = installation.get("team") or {}
    authed_user = installation.get("authed_user") or {}

    slack_team_id = team.get("id")
    slack_team_name = team.get("name") or slack_team_id
    bot_token = installation.get("access_token")

    if not slack_team_id or not bot_token:
        raise HTTPException(status_code=400, detail="Slack did not return a usable workspace installation.")

    existing_workspace = (
        db.query(SlackWorkspace)
        .filter(SlackWorkspace.tenant_id == tenant_id)
        .first()
    )

    if not existing_workspace:
        existing_workspace = SlackWorkspace(
            tenant_id=tenant_id,
            slack_team_id=slack_team_id,
            slack_team_name=slack_team_name,
            bot_token=bot_token,
            bot_user_id=installation.get("bot_user_id"),
            scope=installation.get("scope"),
            connected_by_user_id=connected_by_user_id,
            connected_by_slack_user_id=authed_user.get("id"),
            is_active=True,
        )
        db.add(existing_workspace)
    else:
        existing_workspace.slack_team_id = slack_team_id
        existing_workspace.slack_team_name = slack_team_name
        existing_workspace.bot_token = bot_token
        existing_workspace.bot_user_id = installation.get("bot_user_id")
        existing_workspace.scope = installation.get("scope")
        existing_workspace.connected_by_user_id = connected_by_user_id
        existing_workspace.connected_by_slack_user_id = authed_user.get("id")
        existing_workspace.is_active = True

    db.commit()
    db.refresh(existing_workspace)
    return existing_workspace


def get_workspace_for_tenant(db: Session, tenant_id: str) -> SlackWorkspace | None:
    return (
        db.query(SlackWorkspace)
        .filter(
            SlackWorkspace.tenant_id == tenant_id,
            SlackWorkspace.is_active.is_(True),
        )
        .first()
    )


def list_workspace_channels(workspace: SlackWorkspace) -> list[dict[str, Any]]:
    response = requests.get(
        SLACK_CHANNELS_URL,
        headers={"Authorization": f"Bearer {workspace.bot_token}"},
        params={
            "exclude_archived": "true",
            "limit": 1000,
            "types": "public_channel,private_channel",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    if not payload.get("ok"):
        raise HTTPException(
            status_code=400,
            detail=f"Slack channel lookup failed: {payload.get('error', 'unknown_error')}",
        )

    channels = payload.get("channels") or []
    scopes = _workspace_scopes(workspace)
    normalized = []

    for channel in channels:
        channel_id = channel.get("id")
        if not channel_id:
            continue

        is_private = bool(channel.get("is_private"))
        is_member = bool(channel.get("is_member"))
        is_public_channel = bool(channel.get("is_channel"))
        can_auto_join = is_public_channel and "channels:join" in scopes
        can_public_post = is_public_channel and "chat:write.public" in scopes
        delivery_ready = is_member or can_auto_join or can_public_post

        if is_private and not is_member:
            action_required = "invite_bot"
            readiness_message = "Invite @opssight to this private channel before saving it."
        elif not delivery_ready:
            action_required = "reconnect_slack"
            readiness_message = "Reconnect Slack to grant channels:join or chat:write.public for public-channel delivery."
        else:
            action_required = None
            readiness_message = "Ready to receive incident alerts."

        normalized.append(
            {
                "id": channel_id,
                "name": channel.get("name") or channel_id,
                "is_private": is_private,
                "is_member": is_member,
                "delivery_ready": delivery_ready,
                "action_required": action_required,
                "readiness_message": readiness_message,
            }
        )

    normalized.sort(key=lambda channel: channel["name"].lower())
    return normalized


def save_default_channel(
    db: Session,
    *,
    workspace: SlackWorkspace,
    channel_id: str,
    channel_name: str,
) -> SlackChannel:
    ensure_channel_delivery_ready(workspace, channel_id, channel_name)

    for channel in workspace.channels:
        channel.is_default = False

    selected = (
        db.query(SlackChannel)
        .filter(
            SlackChannel.workspace_id == workspace.id,
            SlackChannel.slack_channel_id == channel_id,
        )
        .first()
    )

    if not selected:
        selected = SlackChannel(
            workspace_id=workspace.id,
            slack_channel_id=channel_id,
            slack_channel_name=channel_name,
            is_default=True,
        )
        db.add(selected)
    else:
        selected.slack_channel_name = channel_name
        selected.is_default = True

    db.commit()
    db.refresh(selected)
    return selected


def disconnect_workspace(db: Session, workspace: SlackWorkspace) -> None:
    db.delete(workspace)
    db.commit()


def get_default_channel(workspace: SlackWorkspace) -> SlackChannel | None:
    return next((channel for channel in workspace.channels if channel.is_default), None)


def _workspace_scopes(workspace: SlackWorkspace) -> set[str]:
    return {
        scope.strip()
        for scope in (workspace.scope or "").split(",")
        if scope.strip()
    }


def get_channel_details(workspace: SlackWorkspace, channel_id: str) -> dict[str, Any]:
    response = requests.get(
        SLACK_CHANNEL_INFO_URL,
        headers={"Authorization": f"Bearer {workspace.bot_token}"},
        params={"channel": channel_id},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    if not payload.get("ok"):
        raise RuntimeError(payload.get("error", "unknown_error"))

    return payload.get("channel") or {}


def ensure_channel_delivery_ready(workspace: SlackWorkspace, channel_id: str, channel_name: str) -> dict[str, Any]:
    channel_info = get_channel_details(workspace, channel_id)

    if channel_info.get("is_private") and not channel_info.get("is_member"):
        raise HTTPException(
            status_code=400,
            detail=(
            f"Slack bot is not a member of private channel #{channel_name}. "
            "Invite @opssight to the channel, then retry."
            ),
        )

    if channel_info.get("is_member"):
        return channel_info

    scopes = _workspace_scopes(workspace)

    if channel_info.get("is_channel") and "channels:join" in scopes:
        join_response = requests.post(
            SLACK_CHANNEL_JOIN_URL,
            headers={
                "Authorization": f"Bearer {workspace.bot_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"channel": channel_id},
            timeout=20,
        )
        join_response.raise_for_status()
        join_payload = join_response.json()

        if not join_payload.get("ok"):
            raise HTTPException(
                status_code=400,
                detail=f"Slack could not auto-join #{channel_name}: {join_payload.get('error', 'unable_to_join_channel')}",
            )

        channel_info = join_payload.get("channel") or channel_info

        if channel_info.get("is_member"):
            return channel_info

    if channel_info.get("is_channel") and "chat:write.public" in scopes:
        return channel_info

    raise HTTPException(
        status_code=400,
        detail=(
        f"Slack bot cannot post to #{channel_name}. "
        "Invite @opssight to the channel or reconnect Slack with channels:join/chat:write.public scopes."
        ),
    )


def build_frontend_callback_url(success: bool, message: str) -> str:
    params = urlencode(
        {
            "connected": "1" if success else "0",
            "message": message,
        }
    )
    return f"{FRONTEND_URL.rstrip('/')}/integrations/slack?{params}"


def _incident_slack_description(incident) -> str:
    description = getattr(incident, "description", "") or ""

    try:
        payload = json.loads(description)
    except (TypeError, json.JSONDecodeError):
        payload = None

    if isinstance(payload, dict):
        description = (
            payload.get("summary")
            or payload.get("recommendation")
            or description
        )

    description = " ".join(str(description).split())
    if len(description) > 500:
        return f"{description[:497]}..."
    return description


def send_incident_notification(db: Session, *, tenant_id: str | None, incident) -> None:
    if not tenant_id:
        tenant_id = resolve_tenant_id_for_run(db, incident.run_id)

    if not tenant_id:
        logger.warning(
            "Skipping incident %s Slack delivery because tenant_id could not be resolved for run %s",
            getattr(incident, "id", None),
            getattr(incident, "run_id", None),
        )
        return

    workspace = get_workspace_for_tenant(db, tenant_id)
    if not workspace:
        notify_tenant_by_email(
            db,
            tenant_id=tenant_id,
            incident=incident,
            delivery_reason="Your workspace does not have Slack connected, so this alert is being delivered by email.",
        )
        return

    default_channel = get_default_channel(workspace)
    if not default_channel:
        notify_tenant_by_email(
            db,
            tenant_id=tenant_id,
            incident=incident,
            delivery_reason="Your workspace does not have a default Slack alert channel configured, so this alert is being delivered by email.",
        )
        return

    try:
        ensure_channel_delivery_ready(
            workspace,
            default_channel.slack_channel_id,
            default_channel.slack_channel_name,
        )
    except Exception as exc:
        logger.warning(
            "Slack channel %s is not ready for incident delivery: %s",
            default_channel.slack_channel_name,
            exc,
        )
        notify_tenant_by_email(
            db,
            tenant_id=tenant_id,
            incident=incident,
            delivery_reason=str(exc),
        )
        return

    text = (
        f":rotating_light: *{incident.severity.upper()} incident*\n"
        f"*Title:* {incident.title}\n"
        f"*Type:* {incident.failure_type}\n"
        f"*Run ID:* {incident.run_id}\n"
        f"*Status:* {incident.status}\n"
        f"*Description:* {_incident_slack_description(incident)}"
    )

    try:
        response = requests.post(
            SLACK_POST_MESSAGE_URL,
            headers={
                "Authorization": f"Bearer {workspace.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "channel": default_channel.slack_channel_id,
                "text": text,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(payload.get("error", "unknown_error"))
        logger.info(
            "Slack incident alert delivered to %s for incident %s",
            default_channel.slack_channel_name,
            incident.id,
        )
    except Exception as exc:
        logger.warning(
            "Slack delivery failed for incident %s on channel %s: %s",
            incident.id,
            default_channel.slack_channel_name,
            exc,
        )
        notify_tenant_by_email(
            db,
            tenant_id=tenant_id,
            incident=incident,
            delivery_reason=f"Slack delivery failed ({exc}), so this alert is being delivered by email.",
        )
        return


def resolve_tenant_id_for_run(db: Session, run_id: int) -> str | None:
    pipeline_run = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == run_id)
        .first()
    )
    if not pipeline_run:
        return None

    model = (
        db.query(MLModel)
        .filter(MLModel.id == pipeline_run.model_id)
        .first()
    )
    if model and model.tenant_id:
        return model.tenant_id

    public_tenant_id = db.execute(
        text("SELECT tenant_id FROM public.ml_models WHERE id = :model_id"),
        {"model_id": pipeline_run.model_id},
    ).scalar()
    if public_tenant_id:
        return public_tenant_id

    current_schema_name = db.execute(text("SELECT current_schema()")).scalar()
    if current_schema_name and current_schema_name != "public":
        tenant = (
            db.query(Tenant)
            .filter(Tenant.schema_name == current_schema_name)
            .first()
        )
        if tenant:
            return tenant.id

    return None


def notify_tenant_by_email(
    db: Session,
    *,
    tenant_id: str,
    incident,
    delivery_reason: str,
) -> None:
    recipients = (
        db.query(User)
        .filter(
            User.tenant_id == tenant_id,
            User.is_verified.is_(True),
        )
        .all()
    )

    for user in recipients:
        if not user.email:
            continue

        send_incident_alert_email_task.delay(
            user.email,
            incident.title,
            incident.severity,
            incident.run_id,
            incident.failure_type,
            incident.status,
            incident.description,
            delivery_reason,
        )
