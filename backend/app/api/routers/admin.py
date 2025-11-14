"""
Admin API endpoints for Veda Healthcare Chatbot.
Provides admin statistics, moderation management, and system monitoring.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
from pydantic import BaseModel
import psutil
import os

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.moderation import moderation_service
from app.services.llm_provider import LLMProvider
from app.services.rag.pipeline import RAGPipeline
from app.core.logging_config import log_admin_action, get_admin_logger

router = APIRouter()
admin_logger = get_admin_logger()

# Track application start time for uptime calculation
app_start_time = datetime.utcnow()


def require_admin_role(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role for protected endpoints."""
    
    if current_user.role != "admin":
        log_admin_action(
            action="unauthorized_access_attempt",
            admin_user_id=str(current_user.id),
            details={"attempted_endpoint": "admin", "user_role": current_user.role}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


@router.get("/stats", response_model=Dict[str, Any])
async def get_admin_stats(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to include in stats"),
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive admin statistics.
    
    Args:
        days: Number of days to include in statistics
        admin_user: Current admin user
        db: Database session
        
    Returns:
        Dictionary containing various system statistics
    """
    
    try:
        # Calculate date range (use timezone-aware datetime)
        from datetime import timezone
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # User statistics
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        new_users_result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= start_date)
        )
        new_users = new_users_result.scalar()
        
        # Conversation statistics
        total_conversations_result = await db.execute(select(func.count(Conversation.id)))
        total_conversations = total_conversations_result.scalar()
        
        recent_conversations_result = await db.execute(
            select(func.count(Conversation.id)).where(Conversation.created_at >= start_date)
        )
        recent_conversations = recent_conversations_result.scalar()
        
        # Message statistics
        total_messages_result = await db.execute(select(func.count(Message.id)))
        total_messages = total_messages_result.scalar()
        
        recent_messages_result = await db.execute(
            select(func.count(Message.id)).where(Message.created_at >= start_date)
        )
        recent_messages = recent_messages_result.scalar()
        
        # User messages vs assistant messages
        user_messages_result = await db.execute(
            select(func.count(Message.id)).where(
                and_(Message.sender == "user", Message.created_at >= start_date)
            )
        )
        user_messages = user_messages_result.scalar()
        
        assistant_messages_result = await db.execute(
            select(func.count(Message.id)).where(
                and_(Message.sender == "assistant", Message.created_at >= start_date)
            )
        )
        assistant_messages = assistant_messages_result.scalar()
        
        # Calculate average messages per conversation
        avg_messages_per_conversation = (
            round(total_messages / total_conversations, 2) 
            if total_conversations > 0 else 0
        )
        
        # Moderation statistics from service (in-memory stats)
        moderation_stats = moderation_service.get_statistics()
        
        # Get real-time database counts for flagged/blocked messages
        total_flagged_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.status.in_(["flagged", "blocked"]))
        )
        total_flagged = total_flagged_result.scalar() or 0
        
        # Count unreviewed flagged messages (needs review)
        reviewed_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.status.in_(["flagged", "blocked"]),
                    Message.message_metadata.op('->>')('reviewed') == 'true'
                )
            )
        )
        reviewed_count = reviewed_result.scalar() or 0
        flagged_needs_review = total_flagged - reviewed_count
        
        # Enhance moderation stats with database counts
        moderation_stats['total_flags'] = total_flagged
        moderation_stats['needs_review'] = flagged_needs_review
        moderation_stats['reviewed'] = reviewed_count
        
        # System health checks
        llm_provider = LLMProvider()
        rag_pipeline = RAGPipeline()
        
        llm_health = await llm_provider.health_check()
        rag_health = await rag_pipeline.health_check()
        moderation_health = moderation_service.health_check()
        
        # Daily activity breakdown
        daily_activity = []
        for day_offset in range(days):
            # Start from (days-1) days ago to today (0 days ago)
            # When days=7: day_offset goes 0,1,2,3,4,5,6
            # Calculate days ago: 0 = today, 1 = yesterday, etc.
            days_ago = days - 1 - day_offset
            day_date = end_date - timedelta(days=days_ago)
            # Ensure we include today's data by using end_date for the last day
            if days_ago == 0:  # Today
                day_start = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = end_date  # Use current time for today
            else:
                day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
            
            # DEBUG: Print date range for today
            if days_ago == 0:
                admin_logger.info(f"TODAY's range: {day_start} to {day_end}")
            
            # Messages on this day
            messages_on_day_result = await db.execute(
                select(func.count(Message.id)).where(
                    and_(Message.created_at >= day_start, Message.created_at < day_end)
                )
            )
            messages_count = messages_on_day_result.scalar() or 0
            
            # DEBUG: Log today's counts
            if days_ago == 0:
                admin_logger.info(f"TODAY's message count: {messages_count}")
            
            # Conversations started on this day
            conversations_on_day_result = await db.execute(
                select(func.count(Conversation.id)).where(
                    and_(Conversation.created_at >= day_start, Conversation.created_at < day_end)
                )
            )
            conversations_count = conversations_on_day_result.scalar() or 0
            
            # DEBUG: Log today's counts
            if days_ago == 0:
                admin_logger.info(f"TODAY's conversation count: {conversations_count}")
            
            # Active users on this day (users who had conversations with messages)
            active_users_on_day_result = await db.execute(
                select(func.count(func.distinct(Conversation.user_id)))
                .join(Message, Message.conversation_id == Conversation.id)
                .where(
                    and_(Message.created_at >= day_start, Message.created_at < day_end)
                )
            )
            active_users_count = active_users_on_day_result.scalar() or 0
            
            daily_activity.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "messages": messages_count,
                "conversations": conversations_count,
                "active_users": active_users_count
            })
        
        # Compile comprehensive stats
        stats = {
            "overview": {
                "total_users": total_users,
                "new_users_last_{}_days".format(days): new_users,
                "total_conversations": total_conversations,
                "recent_conversations": recent_conversations,
                "total_messages": total_messages,
                "recent_messages": recent_messages,
                "user_messages_recent": user_messages,
                "assistant_messages_recent": assistant_messages,
                "avg_messages_per_conversation": avg_messages_per_conversation
            },
            "daily_activity": daily_activity,
            "moderation": moderation_stats,
            "system_health": {
                "llm_provider": llm_health,
                "rag_pipeline": rag_health,
                "moderation_service": moderation_health
            },
            "time_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": str(admin_user.id)
        }
        
        # Log admin action
        log_admin_action(
            action="view_admin_stats",
            admin_user_id=str(admin_user.id),
            details={"days": days, "stats_generated": True}
        )
        
        return stats
        
    except Exception as e:
        admin_logger.exception("Failed to generate admin stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate statistics"
        ) from e


@router.get("/metrics", response_model=Dict[str, Any])
async def get_admin_metrics(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get real-time system metrics for monitoring.
    Returns uptime, active conversations, messages today, flagged messages, and system resources.
    
    Args:
        admin_user: Current admin user
        db: Database session
        
    Returns:
        Dictionary containing real-time metrics
    """
    
    try:
        # Calculate uptime
        current_time = datetime.utcnow()
        uptime_delta = current_time - app_start_time
        uptime_seconds = int(uptime_delta.total_seconds())
        uptime_formatted = str(uptime_delta).split('.')[0]  # Remove microseconds
        
        # Get today's date range
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Active conversations (conversations with messages in last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_conversations_result = await db.execute(
            select(func.count(func.distinct(Message.conversation_id)))
            .where(Message.created_at >= yesterday)
        )
        active_conversations = active_conversations_result.scalar()
        
        # Messages today
        messages_today_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.created_at >= today_start)
        )
        messages_today = messages_today_result.scalar()
        
        # Flagged and blocked messages (total)
        flagged_messages_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.status.in_(["flagged", "blocked"]))
        )
        flagged_messages = flagged_messages_result.scalar()
        
        # Recent flagged messages (last 24 hours)
        recent_flagged_result = await db.execute(
            select(func.count(Message.id))
            .where(and_(
                Message.status == "flagged",
                Message.created_at >= yesterday
            ))
        )
        recent_flagged = recent_flagged_result.scalar()
        
        # System resource metrics
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)
        
        # System-wide metrics
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=0.1)
        
        metrics = {
            "uptime": {
                "seconds": uptime_seconds,
                "formatted": uptime_formatted,
                "started_at": app_start_time.isoformat()
            },
            "conversations": {
                "active_last_24h": active_conversations
            },
            "messages": {
                "today": messages_today,
                "flagged_total": flagged_messages,
                "flagged_last_24h": recent_flagged
            },
            "system_resources": {
                "process": {
                    "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "memory_percent": round(process.memory_percent(), 2),
                    "cpu_percent": round(cpu_percent, 2),
                    "threads": process.num_threads()
                },
                "system": {
                    "memory_total_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                    "memory_available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                    "memory_percent": system_memory.percent,
                    "cpu_percent": system_cpu,
                    "cpu_count": psutil.cpu_count()
                }
            },
            "timestamp": current_time.isoformat(),
            "collected_by": str(admin_user.id)
        }
        
        log_admin_action(
            action="view_metrics",
            admin_user_id=str(admin_user.id),
            details={"metrics_collected": True}
        )
        
        return metrics
        
    except Exception as e:
        admin_logger.exception("Failed to generate metrics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate metrics"
        ) from e


@router.get("/moderation/stats", response_model=Dict[str, Any])
async def get_moderation_stats(
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)  # ✅ ADD THIS
):
    """Get detailed moderation statistics.
    
    Combines moderation service stats with real-time database counts.
    
    Args:
        admin_user: Current admin user
        db: Database session
        
    Returns:
        Detailed moderation statistics and configuration"""
    
    try:
        # Get base stats from moderation service (your original approach)
        service_stats = moderation_service.get_statistics()
        health = moderation_service.health_check()
        
        # ADD: Get real-time database counts
        today = datetime.utcnow().date()
        
        # Count total flagged and blocked messages in database
        total_flagged_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.status.in_(["flagged", "blocked"]))
        )
        total_flagged = total_flagged_result.scalar() or 0
        
        # Count unreviewed flagged and blocked messages
        # Simpler approach: count all flagged/blocked, then subtract those explicitly marked as reviewed
        all_flagged_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.status.in_(["flagged", "blocked"]))
        )
        
        reviewed_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.status.in_(["flagged", "blocked"]),
                    Message.message_metadata.op('->>')('reviewed') == 'true'
                )
            )
        )
        
        flagged_unreviewed = (all_flagged_result.scalar() or 0) - (reviewed_result.scalar() or 0)
        
        # Count flagged messages today
        flagged_today_result = await db.execute(
            select(func.count(Message.id))
            .where(
                and_(
                    Message.status == "flagged",
                    func.date(Message.created_at) == today
                )
            )
        )
        flagged_today = flagged_today_result.scalar() or 0
        
        # ADD: Extract top flagged keywords from database
        result = await db.execute(
            select(Message.message_metadata)
            .where(Message.status.in_(["flagged", "blocked"]))
            .limit(100)  # Sample last 100 flagged/blocked messages
        )
        messages_meta = result.scalars().all()
        
        keyword_count = {}
        for meta in messages_meta:
            if meta and isinstance(meta, dict):
                keywords = meta.get("flagged_keywords", [])
                for kw in keywords:
                    keyword_count[kw] = keyword_count.get(kw, 0) + 1
        
        top_keywords = [
            {"keyword": k, "count": v}
            for k, v in sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # COMBINE: Merge service stats with database stats
        detailed_stats = {
            # Moderation service stats (from your original code)
            **service_stats,
            
            # Add total_rules for frontend compatibility
            "total_rules": service_stats.get("total_keywords", 0),
            
            # Database counts (real-time)
            "database_counts": {
                "total_flagged": total_flagged,
                "flagged_unreviewed": flagged_unreviewed,
                "flagged_today": flagged_today
            },
            
            # Top keywords from database
            "top_keywords": top_keywords,
            
            # Health and rules (from your original code)
            "health": health,
            "rules_breakdown": {
                severity: len(keywords) 
                for severity, keywords in moderation_service.rules.items()
            },
            
            # Metadata
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": str(admin_user.id)
        }
        
        log_admin_action(
            action="view_moderation_stats",
            admin_user_id=str(admin_user.id),
            details={"total_flagged": total_flagged}
        )
        
        return detailed_stats
        
    except Exception as e:
        admin_logger.exception("Failed to get moderation stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation statistics"
        ) from e


@router.post("/moderation/reload-rules", response_model=Dict[str, Any])
async def reload_moderation_rules(
    admin_user: User = Depends(require_admin_role)
):
    """
    Reload moderation rules from file.
    
    Args:
        admin_user: Current admin user
        
    Returns:
        Success status and updated rule counts
    """
    
    try:
        old_count = sum(len(keywords) for keywords in moderation_service.rules.values())
        success = moderation_service.reload_rules()
        new_count = sum(len(keywords) for keywords in moderation_service.rules.values())
        
        if success:
            log_admin_action(
                action="reload_moderation_rules",
                admin_user_id=str(admin_user.id),
                details={"old_count": old_count, "new_count": new_count, "success": True}
            )
            
            return {
                "success": True,
                "message": "Moderation rules reloaded successfully",
                "old_rule_count": old_count,
                "new_rule_count": new_count,
                "reloaded_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload moderation rules"
            )
            
    except Exception as e:
        admin_logger.exception("Failed to reload moderation rules")
        log_admin_action(
            action="reload_moderation_rules",
            admin_user_id=str(admin_user.id),
            details={"success": False, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload moderation rules: {str(e)}"
        ) from e


@router.get("/users", response_model=Dict[str, Any])
async def get_users_list(
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of users to return"),
    offset: int = Query(default=0, ge=0, description="Number of users to skip"),
    search: Optional[str] = Query(default=None, description="Search by email or name"),  # ADD THIS
    role: Optional[str] = Query(default=None, description="Filter by role (admin/user)"), 
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users with pagination, search, and filtering.
    
    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        admin_user: Current admin user
        db: Database session
        
    Returns:
        List of user information dictionaries
    """
    
    try:
        # Build base query
        query = select(User).order_by(desc(User.created_at))
        
        # ADD SEARCH FILTER
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_pattern)) | (User.name.ilike(search_pattern))
            )
        
        # ADD ROLE FILTER
        if role:
            query = query.where(User.role == role)
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        users_result = await db.execute(query)
        users = users_result.scalars().all()
        
        # Get conversation counts for each user
        user_list = []
        for user in users:
            conv_count_result = await db.execute(
                select(func.count(Conversation.id)).where(Conversation.user_id == user.id)
            )
            conv_count = conv_count_result.scalar()
            
            user_list.append({
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "conversation_count": conv_count
            })
        
        # Get total count for pagination
        count_query = select(func.count(User.id))
        if search:
            count_query = count_query.where(
                (User.email.ilike(search_pattern)) | (User.name.ilike(search_pattern))
            )
        if role:
            count_query = count_query.where(User.role == role)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Calculate page number
        page = (offset // limit) + 1 if limit > 0 else 1
        
        log_admin_action(
            action="view_users_list",
            admin_user_id=str(admin_user.id),
            details={
                "limit": limit, 
                "offset": offset, 
                "search": search,
                "role": role,
                "returned_count": len(user_list)
            }
        )
        
        # Return with pagination metadata
        return {
            "users": user_list,
            "total": total or 0,
            "page": page,
            "page_size": limit
        }
        
    except Exception as e:
        admin_logger.exception("Failed to get users list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list"
        ) from e


class FlaggedMessageDetail(BaseModel):
    message_id: str
    sender: str
    content: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None
    reviewed: bool = False

class FlaggedConversationItem(BaseModel):
    conversation_id: str
    user_email: str
    title: Optional[str]
    created_at: str
    flagged_messages: List[FlaggedMessageDetail]
    total_flagged_count: int = 0
    reviewed_count: int = 0
    unreviewed_count: int = 0

class FlaggedConversationsResponse(BaseModel):
    conversations: List[FlaggedConversationItem]
    total: int
    page: int
    page_size: int

@router.get("/moderation/flagged", response_model=FlaggedConversationsResponse)
async def get_flagged_content(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    reviewed: Optional[bool] = Query(default=None, description="Filter by review status (true/false)"),
    user_email: Optional[str] = Query(default=None, description="Filter by user email"),
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get flagged conversations with their flagged messages.
    Returns conversations that contain flagged messages, grouped by conversation.
    """
    try:
        offset = (page - 1) * page_size
        
        # STEP 1: Get ALL flagged and blocked messages to calculate total counts per conversation
        all_flagged_query = select(Message.conversation_id, Message.message_metadata) \
            .where(Message.status.in_(["flagged", "blocked"]))
        
        all_flagged_result = await db.execute(all_flagged_query)
        all_flagged_rows = all_flagged_result.all()
        
        # Calculate total counts per conversation
        conversation_counts = {}
        for row in all_flagged_rows:
            conv_id = str(row.conversation_id)
            if conv_id not in conversation_counts:
                conversation_counts[conv_id] = {"total": 0, "reviewed": 0, "unreviewed": 0}
            
            conversation_counts[conv_id]["total"] += 1
            # Check if reviewed - handle both string 'true' and boolean True
            metadata = row.message_metadata if row.message_metadata else {}
            is_reviewed = metadata.get("reviewed", False)
            # Handle both boolean True and string 'true'
            if is_reviewed is True or is_reviewed == True or str(is_reviewed).lower() == 'true':
                conversation_counts[conv_id]["reviewed"] += 1
            else:
                conversation_counts[conv_id]["unreviewed"] += 1
        
        # STEP 2: Get filtered messages with conversation and user info
        query = select(Message, Conversation, User.email) \
            .join(Conversation, Message.conversation_id == Conversation.id) \
            .join(User, Conversation.user_id == User.id) \
            .where(Message.status.in_(["flagged", "blocked"]))
        
        # Apply user email filter if provided
        if user_email:
            query = query.where(User.email.ilike(f"%{user_email}%"))
        
        # Apply reviewed filter if provided
        if reviewed is not None:
            if reviewed:
                # Messages with reviewed=true in metadata
                query = query.where(
                    Message.message_metadata.op('->>')('reviewed') == 'true'
                )
            else:
                # Messages that don't have reviewed=true in metadata
                query = query.where(
                    or_(
                        Message.message_metadata == None,
                        Message.message_metadata.op('->>')('reviewed') == None,
                        Message.message_metadata.op('->>')('reviewed') != 'true'
                    )
                )
        
        # Order by most recent
        query = query.order_by(desc(Message.created_at))
        
        # Execute query to get filtered flagged messages
        result = await db.execute(query)
        rows = result.all()
        
        # Group messages by conversation
        conversations_dict: Dict[str, Dict] = {}
        
        for row in rows:
            message = row.Message
            conversation = row.Conversation
            user_email = row.email
            
            conv_id = str(conversation.id)
            
            if conv_id not in conversations_dict:
                conversations_dict[conv_id] = {
                    "conversation_id": conv_id,
                    "user_email": user_email,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "flagged_messages": [],
                    "latest_flag_time": message.created_at  # For sorting
                }
            
            # Add flagged message to conversation
            conversations_dict[conv_id]["flagged_messages"].append({
                "message_id": str(message.id),
                "sender": message.sender,
                "content": message.content[:200] + "..." if len(message.content) > 200 else message.content,
                "created_at": message.created_at.isoformat(),
                "metadata": message.message_metadata,
                "reviewed": message.message_metadata.get("reviewed", False) if message.message_metadata else False
            })
            
            # Update latest flag time if this message is more recent
            if message.created_at > conversations_dict[conv_id]["latest_flag_time"]:
                conversations_dict[conv_id]["latest_flag_time"] = message.created_at
        
        # Convert to list and sort by latest flag time
        conversations_list = sorted(
            conversations_dict.values(),
            key=lambda x: x["latest_flag_time"],
            reverse=True
        )
        
        # Add counts for each conversation using pre-calculated totals
        for conv in conversations_list:
            conv_id = conv["conversation_id"]
            counts = conversation_counts.get(conv_id, {"total": 0, "reviewed": 0, "unreviewed": 0})
            
            conv["total_flagged_count"] = counts["total"]
            conv["reviewed_count"] = counts["reviewed"]
            conv["unreviewed_count"] = counts["unreviewed"]
            
            del conv["latest_flag_time"]
        
        # Apply pagination to conversations
        total_conversations = len(conversations_list)
        paginated_conversations = conversations_list[offset:offset + page_size]
        
        log_admin_action(
            action="view_flagged_content",
            admin_user_id=str(admin_user.id),
            details={
                "page": page,
                "page_size": page_size,
                "reviewed_filter": reviewed,
                "user_email_filter": user_email,
                "returned_count": len(paginated_conversations)
            }
        )
        
        return FlaggedConversationsResponse(
            conversations=[
                FlaggedConversationItem(**conv) for conv in paginated_conversations
            ],
            total=total_conversations,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        admin_logger.exception("Failed to get flagged content")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flagged content"
        ) from e
    

@router.patch("/moderation/resolve/{message_id}", response_model=Dict[str, Any])
async def resolve_flagged_message(
    message_id: str,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a flagged message as reviewed by admin.
    Updates the message metadata to include review information.
    """
    try:
        from uuid import UUID
        
        # Convert string to UUID
        try:
            msg_uuid = UUID(message_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message ID format"
            )
        
        # Get the message
        result = await db.execute(
            select(Message).where(Message.id == msg_uuid)
        )
        message = result.scalars().first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message.status != "flagged":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is not flagged"
            )
        
        # Update metadata to mark as reviewed
        metadata = message.message_metadata or {}
        metadata["reviewed"] = True
        metadata["reviewed_by"] = str(admin_user.id)
        metadata["reviewed_by_email"] = admin_user.email
        metadata["reviewed_at"] = datetime.utcnow().isoformat()
        
        message.message_metadata = metadata
        
        # Mark the JSONB column as modified (important for SQLAlchemy to detect the change)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(message, "message_metadata")
        
        await db.commit()
        await db.refresh(message)
        
        log_admin_action(
            action="resolve_flagged_message",
            admin_user_id=str(admin_user.id),
            details={"reviewed": True, "message_id": message_id}
        )
        
        return {
            "success": True,
            "message": "Flagged message marked as reviewed",
            "message_id": message_id,
            "reviewed_at": metadata["reviewed_at"],
            "reviewed_by": admin_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        admin_logger.exception("Failed to resolve flagged message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve flagged message"
        ) from e


@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health(
    admin_user: User = Depends(require_admin_role)
):
    """
    Get comprehensive system health status.
    
    Args:
        admin_user: Current admin user
        
    Returns:
        System health information
    """
    
    try:
        # Get health status from all components
        llm_provider = LLMProvider()
        rag_pipeline = RAGPipeline()
        
        llm_health = await llm_provider.health_check()
        rag_health = await rag_pipeline.health_check()
        moderation_health = moderation_service.health_check()
        
        # Overall system status
        all_healthy = all([
            llm_health.get("status") == "healthy",
            rag_health.get("status") == "healthy",
            moderation_health.get("status") == "healthy"
        ])
        
        system_health = {
            "overall_status": "healthy" if all_healthy else "degraded",
            "components": {
                "llm_provider": llm_health,
                "rag_pipeline": rag_health,
                "moderation_service": moderation_health
            },
            "checked_at": datetime.utcnow().isoformat(),
            "checked_by": str(admin_user.id)
        }
        
        log_admin_action(
            action="system_health_check",
            admin_user_id=str(admin_user.id),
            details={"overall_status": system_health["overall_status"]}
        )
        
        return system_health
        
    except Exception as e:
        admin_logger.exception("Failed to get system health")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        ) from e


@router.post("/users/{user_id}/role", response_model=Dict[str, Any])
async def update_user_role(
    user_id: str,
    new_role: str,
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's role (admin only).
    
    Args:
        user_id: ID of the user to update
        new_role: New role to assign
        admin_user: Current admin user
        db: Database session
        
    Returns:
        Success status and updated user information
    """
    
    if new_role not in ["user", "admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user', 'admin', or 'moderator'"
        )
    
    try:
        # Get the target user
        user_result = await db.execute(select(User).where(User.id == user_id))
        target_user = user_result.scalar_one_or_none()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from demoting themselves
        if str(target_user.id) == str(admin_user.id) and new_role != "admin":
            log_admin_action(
                action="attempted_self_demotion",
                admin_user_id=str(admin_user.id),
                details={"attempted_role": new_role, "blocked": True}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own admin role. This action is prevented for security reasons."
            )
        
        old_role = target_user.role
        target_user.role = new_role
        
        await db.commit()
        await db.refresh(target_user)
        
        log_admin_action(
            action="update_user_role",
            admin_user_id=str(admin_user.id),
            target_user_id=user_id,
            details={"old_role": old_role, "new_role": new_role}
        )
        
        return {
            "success": True,
            "message": f"User role updated from {old_role} to {new_role}",
            "user_id": user_id,
            "old_role": old_role,
            "new_role": new_role,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        admin_logger.exception("Failed to update user role")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        ) from e



