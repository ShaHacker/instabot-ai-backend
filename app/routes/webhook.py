from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import async_session
from app.models.ig_account import IGAccount
from app.models.post import Post
from app.models.keyword import Keyword
from app.models.qa_pair import QAPair
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.dm_flow import DMFlow
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.services.gemini_ai import match_comment_to_keywords, match_comment_to_qa, generate_smart_reply
from app.services.instagram import reply_to_comment, send_dm
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Webhook verification endpoint for Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_WEBHOOK_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def handle_webhook(request: Request):
    """Handle incoming webhook events from Instagram (comments and messages)."""
    body = await request.json()
    logger.info(f"Webhook received: {body}")

    try:
        obj = body.get("object")
        entries = body.get("entry", [])

        for entry in entries:
            if obj == "instagram":
                # Handle comment events
                changes = entry.get("changes", [])
                for change in changes:
                    if change.get("field") == "comments":
                        await _handle_comment(change.get("value", {}))

                # Handle messaging events
                messaging = entry.get("messaging", [])
                for msg_event in messaging:
                    await _handle_message(msg_event)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)

    # Always return 200 to acknowledge receipt
    return {"status": "ok"}


async def _handle_comment(comment_data: dict):
    """Process an incoming Instagram comment."""
    media_id = comment_data.get("media", {}).get("id")
    comment_id = comment_data.get("id")
    comment_text = comment_data.get("text", "")
    commenter_username = comment_data.get("from", {}).get("username", "unknown")
    commenter_id = comment_data.get("from", {}).get("id")

    if not media_id or not comment_text:
        return

    async with async_session() as db:
        try:
            # Find the post in our database
            result = await db.execute(
                select(Post).options(selectinload(Post.keywords)).where(Post.ig_post_id == media_id)
            )
            post = result.scalar_one_or_none()
            if not post or not post.automation_enabled:
                return

            # Get the user and their IG account
            user_result = await db.execute(select(User).where(User.id == post.user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return

            ig_result = await db.execute(select(IGAccount).where(IGAccount.user_id == user.id))
            ig_account = ig_result.scalar_one_or_none()
            if not ig_account:
                return

            api_key = user.gemini_api_key

            # Step 1: Try keyword matching
            keywords_data = [{"keyword": k.keyword, "reply_text": k.reply_text, "reply_type": k.reply_type} for k in post.keywords]
            matched_keyword = await match_comment_to_keywords(comment_text, keywords_data, api_key)

            if matched_keyword:
                reply_text = matched_keyword["reply_text"]
                reply_type = matched_keyword["reply_type"]

                if reply_type in ("comment", "both"):
                    await reply_to_comment(comment_id, reply_text, ig_account.page_access_token)
                    _log = ActivityLog(
                        user_id=user.id, action_type="comment_reply",
                        details=f"Replied to @{commenter_username}: {reply_text[:100]}",
                        post_id=post.id, ig_username=commenter_username,
                    )
                    db.add(_log)

                if reply_type in ("dm", "both") and commenter_id:
                    await send_dm(ig_account.ig_user_id, commenter_id, reply_text, ig_account.page_access_token)
                    _log = ActivityLog(
                        user_id=user.id, action_type="dm_sent",
                        details=f"DM sent to @{commenter_username}: {reply_text[:100]}",
                        post_id=post.id, ig_username=commenter_username,
                    )
                    db.add(_log)

                    # Start DM flow if configured
                    await _start_dm_flow(db, user, ig_account, commenter_id, commenter_username, post)

                await db.commit()
                return

            # Step 2: Try Q&A matching
            qa_result = await db.execute(select(QAPair).where(QAPair.user_id == user.id))
            qa_pairs = qa_result.scalars().all()
            qa_data = [{"question": qa.question, "answer": qa.answer} for qa in qa_pairs]
            matched_qa = await match_comment_to_qa(comment_text, qa_data, api_key)

            if matched_qa:
                reply_text = matched_qa["answer"]
                await reply_to_comment(comment_id, reply_text, ig_account.page_access_token)
                _log = ActivityLog(
                    user_id=user.id, action_type="comment_reply",
                    details=f"Q&A reply to @{commenter_username}: {reply_text[:100]}",
                    post_id=post.id, ig_username=commenter_username,
                )
                db.add(_log)
                await db.commit()
                return

        except Exception as e:
            logger.error(f"Comment processing error: {e}", exc_info=True)
            await db.rollback()


async def _handle_message(msg_event: dict):
    """Process an incoming Instagram DM."""
    sender_id = msg_event.get("sender", {}).get("id")
    recipient_id = msg_event.get("recipient", {}).get("id")
    message = msg_event.get("message", {})
    message_text = message.get("text", "")

    if not sender_id or not message_text:
        return

    async with async_session() as db:
        try:
            # Find the IG account this message was sent to
            ig_result = await db.execute(
                select(IGAccount).where(IGAccount.ig_user_id == recipient_id)
            )
            ig_account = ig_result.scalar_one_or_none()
            if not ig_account:
                return

            user_result = await db.execute(select(User).where(User.id == ig_account.user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return

            # Check if there's an active conversation/flow for this sender
            conv_result = await db.execute(
                select(Conversation).join(Lead).where(
                    Conversation.ig_sender_id == sender_id,
                    Lead.user_id == user.id,
                    Conversation.status == "active",
                )
            )
            conversation = conv_result.scalar_one_or_none()

            if conversation:
                await _continue_dm_flow(db, user, ig_account, conversation, sender_id, message_text)
            else:
                # Try Q&A matching for DMs
                qa_result = await db.execute(select(QAPair).where(QAPair.user_id == user.id))
                qa_pairs = qa_result.scalars().all()
                qa_data = [{"question": qa.question, "answer": qa.answer} for qa in qa_pairs]
                matched_qa = await match_comment_to_qa(message_text, qa_data, user.gemini_api_key)

                if matched_qa:
                    await send_dm(ig_account.ig_user_id, sender_id, matched_qa["answer"], ig_account.page_access_token)
                    _log = ActivityLog(
                        user_id=user.id, action_type="dm_sent",
                        details=f"Q&A DM reply to {sender_id}: {matched_qa['answer'][:100]}",
                        ig_username=sender_id,
                    )
                    db.add(_log)
                else:
                    # Generate a smart reply using AI
                    reply = await generate_smart_reply(
                        message_text, "Instagram DM conversation",
                        tone=user.ai_tone or "friendly",
                        custom_tone=user.custom_tone,
                        language=user.default_language or "English",
                        api_key=user.gemini_api_key,
                    )
                    await send_dm(ig_account.ig_user_id, sender_id, reply, ig_account.page_access_token)
                    _log = ActivityLog(
                        user_id=user.id, action_type="dm_sent",
                        details=f"AI DM reply to {sender_id}: {reply[:100]}",
                        ig_username=sender_id,
                    )
                    db.add(_log)

            await db.commit()

        except Exception as e:
            logger.error(f"Message processing error: {e}", exc_info=True)
            await db.rollback()


async def _start_dm_flow(db, user: User, ig_account: IGAccount, sender_id: str, username: str, post: Post):
    """Start a DM flow for lead collection."""
    # Find an active flow for this user
    flow_result = await db.execute(
        select(DMFlow).where(DMFlow.user_id == user.id, DMFlow.is_active == True).limit(1)
    )
    flow = flow_result.scalar_one_or_none()
    if not flow or not flow.steps:
        return

    # Create a lead
    lead = Lead(
        user_id=user.id,
        ig_username=username,
        source_post_id=post.id,
        product=post.caption[:100] if post.caption else None,
        status="new",
    )
    db.add(lead)
    await db.flush()

    # Create conversation
    conversation = Conversation(
        lead_id=lead.id,
        flow_id=flow.id,
        ig_sender_id=sender_id,
        messages=[],
        current_step=0,
    )
    db.add(conversation)
    await db.flush()

    # Send the first flow message
    first_step = flow.steps[0]
    bot_message = first_step.get("bot_message", "Thanks for your interest!")
    await send_dm(ig_account.ig_user_id, sender_id, bot_message, ig_account.page_access_token)

    conversation.messages = [{"role": "bot", "text": bot_message}]

    _log = ActivityLog(
        user_id=user.id, action_type="flow_started",
        details=f"Started flow '{flow.name}' with @{username}",
        post_id=post.id, ig_username=username,
    )
    db.add(_log)

    _log2 = ActivityLog(
        user_id=user.id, action_type="lead_created",
        details=f"New lead: @{username}",
        post_id=post.id, ig_username=username,
    )
    db.add(_log2)


async def _continue_dm_flow(db, user: User, ig_account: IGAccount, conversation: Conversation, sender_id: str, user_message: str):
    """Continue an active DM flow conversation."""
    flow_result = await db.execute(select(DMFlow).where(DMFlow.id == conversation.flow_id))
    flow = flow_result.scalar_one_or_none()
    if not flow:
        return

    steps = flow.steps
    current_step = conversation.current_step

    # Save the user's response
    messages = list(conversation.messages or [])
    messages.append({"role": "user", "text": user_message})

    # Save the field value to the lead
    if current_step < len(steps):
        step = steps[current_step]
        field_name = step.get("field_name", "custom")

        lead_result = await db.execute(select(Lead).where(Lead.id == conversation.lead_id))
        lead = lead_result.scalar_one_or_none()
        if lead:
            if field_name == "name":
                lead.full_name = user_message
            elif field_name == "phone":
                lead.phone = user_message
            elif field_name == "city":
                lead.city = user_message

    # Move to next step
    next_step = current_step + 1

    if next_step < len(steps):
        # Send next question
        bot_message = steps[next_step].get("bot_message", "Please continue...")
        await send_dm(ig_account.ig_user_id, sender_id, bot_message, ig_account.page_access_token)
        messages.append({"role": "bot", "text": bot_message})
        conversation.current_step = next_step
    else:
        # Flow completed
        completion_msg = "Thanks for sharing your details! We'll get back to you soon. ✅"
        await send_dm(ig_account.ig_user_id, sender_id, completion_msg, ig_account.page_access_token)
        messages.append({"role": "bot", "text": completion_msg})
        conversation.status = "completed"

        _log = ActivityLog(
            user_id=user.id, action_type="lead_created",
            details=f"Lead collection completed for {sender_id}",
            ig_username=sender_id,
        )
        db.add(_log)

    conversation.messages = messages
