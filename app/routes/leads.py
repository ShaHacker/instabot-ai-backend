from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.lead import Lead
from app.models.post import Post
from app.schemas.leads import LeadResponse, LeadStatusUpdate, LeadListResponse
from app.services.auth import get_current_user
from io import BytesIO
import openpyxl

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("", response_model=LeadListResponse)
async def list_leads(
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).where(Lead.user_id == user.id)
    count_query = select(func.count(Lead.id)).where(Lead.user_id == user.id)

    if status:
        query = query.where(Lead.status == status)
        count_query = count_query.where(Lead.status == status)
    if search:
        search_filter = Lead.ig_username.ilike(f"%{search}%") | Lead.full_name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Lead.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    leads = result.scalars().all()

    lead_responses = []
    for lead in leads:
        source_caption = None
        if lead.source_post_id:
            post_result = await db.execute(select(Post.caption).where(Post.id == lead.source_post_id))
            source_caption = post_result.scalar_one_or_none()

        lead_responses.append(LeadResponse(
            id=lead.id,
            ig_username=lead.ig_username,
            full_name=lead.full_name,
            phone=lead.phone,
            city=lead.city,
            product=lead.product,
            source_post_id=lead.source_post_id,
            source_post_caption=source_caption,
            status=lead.status,
            notes=lead.notes,
            created_at=lead.created_at,
        ))

    pages = (total + per_page - 1) // per_page if total > 0 else 1
    return LeadListResponse(leads=lead_responses, total=total, page=page, pages=pages)


@router.put("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: int,
    data: LeadStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.user_id == user.id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if data.status not in ("new", "contacted", "converted"):
        raise HTTPException(status_code=400, detail="Invalid status")

    lead.status = data.status
    return LeadResponse(
        id=lead.id,
        ig_username=lead.ig_username,
        full_name=lead.full_name,
        phone=lead.phone,
        city=lead.city,
        product=lead.product,
        source_post_id=lead.source_post_id,
        status=lead.status,
        notes=lead.notes,
        created_at=lead.created_at,
    )


@router.get("/export/excel")
async def export_leads_excel(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead).where(Lead.user_id == user.id).order_by(Lead.created_at.desc())
    )
    leads = result.scalars().all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leads"

    headers = ["ID", "Instagram Username", "Full Name", "Phone", "City", "Product", "Status", "Date"]
    ws.append(headers)

    for lead in leads:
        ws.append([
            lead.id,
            lead.ig_username,
            lead.full_name or "",
            lead.phone or "",
            lead.city or "",
            lead.product or "",
            lead.status,
            lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "",
        ])

    # Auto-size columns
    for col in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"},
    )
