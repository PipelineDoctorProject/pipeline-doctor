from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.tenant import Tenant
from app.schemas.slack import SlackChannelSelectionRequest, SlackConnectResponse
from app.services.slack_service import (
    build_connect_url,
    build_frontend_callback_url,
    decode_oauth_state,
    disconnect_workspace,
    exchange_code_for_installation,
    ensure_channel_delivery_ready,
    get_default_channel,
    get_channel_details,
    get_workspace_for_tenant,
    list_workspace_channels,
    save_default_channel,
    upsert_workspace_installation,
    validate_expected_workspace,
)
from app.utils.schema_utils import set_schema

router = APIRouter(prefix="/slack", tags=["Slack"])


def _require_admin(user) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only workspace admins can manage Slack.")


def _use_current_tenant_schema(db: Session, user) -> None:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == user.tenant_id)
        .first()
    )
    if not tenant or not tenant.schema_name:
        raise HTTPException(status_code=403, detail="Workspace not found.")

    set_schema(db, tenant.schema_name)


@router.get("/connect", response_model=SlackConnectResponse)
def create_connect_url(
    workspace_name: str | None = Query(default=None, min_length=1, max_length=120),
    slack_team_id: str | None = Query(default=None, max_length=32),
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    _require_admin(current_user)
    return {
        "connect_url": build_connect_url(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            expected_team_name=workspace_name,
            expected_team_id=slack_team_id,
        )
    }


@router.get("/callback")
def slack_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(build_frontend_callback_url(False, f"Slack authorization was cancelled: {error}"))

    if not code or not state:
        return RedirectResponse(build_frontend_callback_url(False, "Slack did not return a valid authorization response."))

    try:
        state_payload = decode_oauth_state(state)
        tenant = (
            db.query(Tenant)
            .filter(Tenant.id == state_payload["tenant_id"])
            .first()
        )
        if not tenant or not tenant.schema_name:
            return RedirectResponse(build_frontend_callback_url(False, "Slack connection failed because the workspace no longer exists."))

        set_schema(db, tenant.schema_name)
        installation = exchange_code_for_installation(code)
        validate_expected_workspace(
            installation,
            expected_team_name=state_payload.get("expected_team_name"),
            expected_team_id=state_payload.get("expected_team_id"),
        )
        upsert_workspace_installation(
            db,
            tenant_id=state_payload["tenant_id"],
            connected_by_user_id=state_payload["user_id"],
            installation=installation,
        )
    except HTTPException as exc:
        return RedirectResponse(build_frontend_callback_url(False, str(exc.detail)))
    except Exception:
        return RedirectResponse(build_frontend_callback_url(False, "Slack connection failed unexpectedly."))

    return RedirectResponse(build_frontend_callback_url(True, "Slack workspace connected successfully."))


@router.get("/status")
def get_slack_status(
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    _use_current_tenant_schema(db, current_user)
    workspace = get_workspace_for_tenant(db, current_user.tenant_id)
    default_channel = get_default_channel(workspace) if workspace else None
    default_channel_status = None

    if workspace and default_channel:
        try:
            channel_info = get_channel_details(workspace, default_channel.slack_channel_id)
            ensure_channel_delivery_ready(
                workspace,
                default_channel.slack_channel_id,
                default_channel.slack_channel_name,
            )
            default_channel_status = {
                "delivery_ready": True,
                "is_private": bool(channel_info.get("is_private")),
                "is_member": bool(channel_info.get("is_member")),
                "message": "Slack alerts are ready for this channel.",
            }
        except HTTPException as exc:
            channel_info = channel_info if "channel_info" in locals() else {}
            default_channel_status = {
                "delivery_ready": False,
                "is_private": bool(channel_info.get("is_private")),
                "is_member": bool(channel_info.get("is_member")),
                "message": exc.detail,
            }

    return {
        "connected": bool(workspace),
        "can_manage": current_user.role == "admin",
        "recommended_scopes": [
            "chat:write",
            "chat:write.public",
            "channels:read",
            "channels:join",
            "groups:read",
        ],
        "workspace": (
            {
                "id": workspace.id,
                "slack_team_id": workspace.slack_team_id,
                "slack_team_name": workspace.slack_team_name,
                "connected_by_user_id": workspace.connected_by_user_id,
                "connected_by_slack_user_id": workspace.connected_by_slack_user_id,
                "scope": workspace.scope,
            }
            if workspace
            else None
        ),
        "default_channel": (
            {
                "id": default_channel.id,
                "slack_channel_id": default_channel.slack_channel_id,
                "slack_channel_name": default_channel.slack_channel_name,
                "status": default_channel_status,
            }
            if default_channel
            else None
        ),
    }


@router.get("/channels")
def get_slack_channels(
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    _require_admin(current_user)
    _use_current_tenant_schema(db, current_user)
    workspace = get_workspace_for_tenant(db, current_user.tenant_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Slack is not connected for this workspace.")

    return {"channels": list_workspace_channels(workspace)}


@router.put("/default-channel")
def update_default_channel(
    data: SlackChannelSelectionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    _require_admin(current_user)
    _use_current_tenant_schema(db, current_user)
    workspace = get_workspace_for_tenant(db, current_user.tenant_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Slack is not connected for this workspace.")

    channel = save_default_channel(
        db,
        workspace=workspace,
        channel_id=data.channel_id,
        channel_name=data.channel_name,
    )
    return {
        "message": "Default Slack channel saved.",
        "channel": {
            "id": channel.id,
            "slack_channel_id": channel.slack_channel_id,
            "slack_channel_name": channel.slack_channel_name,
        },
    }


@router.delete("/disconnect")
def remove_slack_connection(
    db: Session = Depends(get_db),
    current_user=Depends(require_tenant_user),
):
    _require_admin(current_user)
    _use_current_tenant_schema(db, current_user)
    workspace = get_workspace_for_tenant(db, current_user.tenant_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Slack is not connected for this workspace.")

    disconnect_workspace(db, workspace)
    return {"message": "Slack workspace disconnected."}
