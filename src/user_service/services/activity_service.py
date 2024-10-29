from typing import Optional, Tuple, List
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from flask import Request
from src.shared import db
from src.user_service.models import UserActivity, User

class ActivityService:
    @staticmethod
    def log_activity(
        user_id: int,
        activity_type: str,
        request: Request,
        status: str = 'success',
        details: dict = None
    ) -> Tuple[Optional[UserActivity], Optional[str]]:
        """Log a user activity"""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status=status,
                details=details or {}
            )
            
            db.session.add(activity)
            db.session.commit()
            
            return activity, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_user_activities(
        user_id: int,
        activity_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Tuple[Optional[List[UserActivity]], Optional[str]]:
        """Get activities for a specific user with optional filters"""
        try:
            query = UserActivity.query.filter_by(user_id=user_id)
            
            if activity_type:
                query = query.filter_by(activity_type=activity_type)
            
            if start_date:
                query = query.filter(UserActivity.created_at >= start_date)
            
            if end_date:
                query = query.filter(UserActivity.created_at <= end_date)
            
            activities = query.order_by(UserActivity.created_at.desc()).all()
            return activities, None
            
        except SQLAlchemyError as e:
            return None, str(e)

    @staticmethod
    def get_all_activities(
        activity_type: str = None,
        status: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Tuple[Optional[List[UserActivity]], Optional[str]]:
        """Get all activities with optional filters (admin only)"""
        try:
            query = UserActivity.query
            
            if activity_type:
                query = query.filter_by(activity_type=activity_type)
            
            if status:
                query = query.filter_by(status=status)
            
            if start_date:
                query = query.filter(UserActivity.created_at >= start_date)
            
            if end_date:
                query = query.filter(UserActivity.created_at <= end_date)
            
            activities = query.order_by(UserActivity.created_at.desc()).all()
            return activities, None
            
        except SQLAlchemyError as e:
            return None, str(e)