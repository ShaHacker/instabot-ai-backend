from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.qa_pair import QAPair
from app.schemas.qa import QACreate, QAUpdate, QAResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/qa", tags=["Q&A Bank"])


@router.get("", response_model=list[QAResponse])
async def list_qa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(QAPair).where(QAPair.user_id == user.id).order_by(QAPair.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=QAResponse)
async def create_qa(data: QACreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    qa = QAPair(user_id=user.id, question=data.question, answer=data.answer)
    db.add(qa)
    await db.flush()
    return qa


@router.put("/{qa_id}", response_model=QAResponse)
async def update_qa(qa_id: int, data: QAUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QAPair).where(QAPair.id == qa_id, QAPair.user_id == user.id))
    qa = result.scalar_one_or_none()
    if not qa:
        raise HTTPException(status_code=404, detail="Q&A pair not found")

    if data.question is not None:
        qa.question = data.question
    if data.answer is not None:
        qa.answer = data.answer
    return qa


@router.delete("/{qa_id}")
async def delete_qa(qa_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QAPair).where(QAPair.id == qa_id, QAPair.user_id == user.id))
    qa = result.scalar_one_or_none()
    if not qa:
        raise HTTPException(status_code=404, detail="Q&A pair not found")

    await db.delete(qa)
    return {"detail": "Q&A pair deleted"}
