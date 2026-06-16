"""Setup / onboarding endpoints.

Powers the Setup wizard so a user can point InfraMind at their own AWS or Azure
subscription: inspect each connector's mode, SDK availability and credential status,
switch a connector between ``mock`` and ``live``, and test the live connection.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.connectors import registry, runtime

router = APIRouter()


class ConnectorSetupStatus(BaseModel):
    name: str
    enabled: bool
    capabilities: list[str]
    description: str
    mode: str  # effective mode (mock|live)
    requested_mode: str  # what the user asked for (may differ if live unusable)
    has_live: bool
    sdk_available: bool
    credentials_detected: bool


class SetupStatus(BaseModel):
    connectors: list[ConnectorSetupStatus]


class ModeRequest(BaseModel):
    mode: str


def _status_for(name: str) -> ConnectorSetupStatus:
    conn = registry.get(name)
    live_cls = registry.live_class(name)
    has_live = live_cls is not None
    sdk_available = bool(has_live and getattr(live_cls, "sdk_available", lambda: False)())
    creds = bool(has_live and getattr(live_cls, "credentials_detected", lambda: False)())
    return ConnectorSetupStatus(
        name=name,
        enabled=registry.is_enabled(name),
        capabilities=[c.value for c in conn.capabilities],
        description=conn.description,
        mode=registry.mode(name),
        requested_mode=runtime.get_mode(name),
        has_live=has_live,
        sdk_available=sdk_available,
        credentials_detected=creds,
    )


@router.get("/status", response_model=SetupStatus)
def status() -> SetupStatus:
    return SetupStatus(connectors=[_status_for(n) for n in registry.all_names()])


@router.post("/connectors/{name}/mode", response_model=ConnectorSetupStatus)
def set_mode(name: str, body: ModeRequest) -> ConnectorSetupStatus:
    if name not in registry.all_names():
        raise HTTPException(status_code=404, detail=f"Unknown connector: {name}")
    try:
        runtime.set_mode(name, body.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _status_for(name)


@router.post("/connectors/{name}/test")
async def test_connector(name: str) -> dict:
    if name not in registry.all_names():
        raise HTTPException(status_code=404, detail=f"Unknown connector: {name}")
    live_cls = registry.live_class(name)
    if live_cls is None:
        return {"ok": False, "detail": "This connector has no live implementation yet (mock only)."}
    conn = live_cls()
    tester = getattr(conn, "test_connection", None)
    if tester is None:
        return {"ok": False, "detail": "Live connector does not support connection testing."}
    return await tester()
