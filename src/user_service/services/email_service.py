# src/user_service/services/email_service.py

from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class EmailService:
    @staticmethod
    def send_password_reset_email(email: str, token: str, expiry: datetime) -> None:
        """Send password reset email (placeholder)"""
        # Add very visible logging
        logger.info("\n")
        logger.info("="*50)
        logger.info("PASSWORD RESET EMAIL - DEVELOPMENT MODE")
        logger.info("="*50)
        logger.info(f"TO: {email}")
        logger.info(f"RESET TOKEN: {token}")
        logger.info(f"EXPIRES AT: {expiry}")
        logger.info(f"USE THIS CURL COMMAND TO RESET:")
        logger.info(f'curl -X POST "http://localhost:5001/api/users/password/reset" -H "Content-Type: application/json" -d {{"token":"{token}","new_password":"NewTest123!@#"}}')
        logger.info("="*50)
        logger.info("\n")
