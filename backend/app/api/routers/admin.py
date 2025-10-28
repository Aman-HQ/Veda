"""
Admin API endpoints for Veda Healthcare Chatbot.
Provides admin statistics, moderation management, and system monitoring.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
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
        # Calculate date range
        end_date = datetime.utcnow()
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
        
        # Moderation statistics
        moderation_stats = moderation_service.get_statistics()
        
        # System health checks
        llm_provider = LLMProvider()
        rag_pipeline = RAGPipeline()
        
        llm_health = await llm_provider.health_check()
        rag_health = await rag_pipeline.health_check()
        moderation_health = moderation_service.health_check()
        
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
                "assistant_messages_recent": assistant_messages
            },
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
        admin_logger.error(f"Failed to generate admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate statistics"
        )


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
        
        # Flagged messages (total)
        flagged_messages_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.status == "flagged")
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
        admin_logger.error(f"Failed to generate metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate metrics"
        )


@router.get("/moderation/stats", response_model=Dict[str, Any])
async def get_moderation_stats(
    admin_user: User = Depends(require_admin_role)
):
    """
    Get detailed moderation statistics.
    
    Args:
        admin_user: Current admin user
        
    Returns:
        Detailed moderation statistics and configuration
    """
    
    try:
        stats = moderation_service.get_statistics()
        health = moderation_service.health_check()
        
        detailed_stats = {
            **stats,
            "health": health,
            "rules_breakdown": {
                severity: len(keywords) 
                for severity, keywords in moderation_service.rules.items()
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        log_admin_action(
            action="view_moderation_stats",
            admin_user_id=str(admin_user.id)
        )
        
        return detailed_stats
        
    except Exception as e:
        admin_logger.error(f"Failed to get moderation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation statistics"
        )


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
        admin_logger.error(f"Failed to reload moderation rules: {e}")
        log_admin_action(
            action="reload_moderation_rules",
            admin_user_id=str(admin_user.id),
            details={"success": False, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload moderation rules: {str(e)}"
        )


@router.get("/users", response_model=List[Dict[str, Any]])
async def get_users_list(
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of users to return"),
    offset: int = Query(default=0, ge=0, description="Number of users to skip"),
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users with basic information.
    
    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        admin_user: Current admin user
        db: Database session
        
    Returns:
        List of user information dictionaries
    """
    
    try:
        # Get users with pagination
        users_result = await db.execute(
            select(User)
            .order_by(desc(User.created_at))
            .limit(limit)
            .offset(offset)
        )
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
        
        log_admin_action(
            action="view_users_list",
            admin_user_id=str(admin_user.id),
            details={"limit": limit, "offset": offset, "returned_count": len(user_list)}
        )
        
        return user_list
        
    except Exception as e:
        admin_logger.error(f"Failed to get users list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list"
        )


@router.get("/conversations/flagged", response_model=List[Dict[str, Any]])
async def get_flagged_conversations(
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of conversations to return"),
    admin_user: User = Depends(require_admin_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversations that have been flagged by moderation.
    
    Args:
        limit: Maximum number of conversations to return
        admin_user: Current admin user
        db: Database session
        
    Returns:
        List of flagged conversation information
    """
    
    try:
        # Get messages that have been flagged
        flagged_messages_result = await db.execute(
            select(Message)
            .where(Message.status == "flagged")
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        flagged_messages = flagged_messages_result.scalars().all()
        
        # Group by conversation and get conversation details
        conversations = {}
        for message in flagged_messages:
            conv_id = str(message.conversation_id)
            if conv_id not in conversations:
                # Get conversation details
                conv_result = await db.execute(
                    select(Conversation).where(Conversation.id == message.conversation_id)
                )
                conversation = conv_result.scalar_one_or_none()
                
                if conversation:
                    conversations[conv_id] = {
                        "conversation_id": conv_id,
                        "title": conversation.title,
                        "created_at": conversation.created_at.isoformat(),
                        "user_id": str(conversation.user_id),
                        "flagged_messages": []
                    }
            
            if conv_id in conversations:
                conversations[conv_id]["flagged_messages"].append({
                    "message_id": str(message.id),
                    "sender": message.sender,
                    "content_preview": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                    "created_at": message.created_at.isoformat(),
                    "metadata": message.message_metadata
                })
        
        result = list(conversations.values())
        
        log_admin_action(
            action="view_flagged_conversations",
            admin_user_id=str(admin_user.id),
            details={"limit": limit, "returned_count": len(result)}
        )
        
        return result
        
    except Exception as e:
        admin_logger.error(f"Failed to get flagged conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flagged conversations"
        )


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
        admin_logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        )


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
        admin_logger.error(f"Failed to update user role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )
