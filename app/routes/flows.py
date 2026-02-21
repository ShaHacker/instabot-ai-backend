from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.dm_flow import DMFlow
from app.schemas.flows import FlowCreate, FlowUpdate, FlowResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/flows", tags=["DM Flows"])


@router.get("", response_model=list[FlowResponse])
async def list_flows(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DMFlow).where(DMFlow.user_id == user.id).order_by(DMFlow.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=FlowResponse)
async def create_flow(data: FlowCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    steps_data = [step.model_dump() for step in data.steps]
    flow = DMFlow(user_id=user.id, name=data.name, steps=steps_data)
    db.add(flow)
    await db.flush()
    return flow


@router.put("/{flow_id}", response_model=FlowResponse)
async def update_flow(flow_id: int, data: FlowUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DMFlow).where(DMFlow.id == flow_id, DMFlow.user_id == user.id))
    flow = result.scalar_one_or_none()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    if data.name is not None:
        flow.name = data.name
    if data.steps is not None:
        flow.steps = [step.model_dump() for step in data.steps]
    if data.is_active is not None:
        flow.is_active = data.is_active
    return flow


@router.delete("/{flow_id}")
async def delete_flow(flow_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DMFlow).where(DMFlow.id == flow_id, DMFlow.user_id == user.id))
    flow = result.scalar_one_or_none()
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    await db.delete(flow)
    return {"detail": "Flow deleted"}
