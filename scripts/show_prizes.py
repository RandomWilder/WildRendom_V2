# scripts/show_prizes.py

from pathlib import Path
import sys
from datetime import datetime
from tabulate import tabulate
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config
from src.prize_service.models import Prize, PrizeType, PrizeStatus, PrizeTier

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "N/A"
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_value(value):
    """Format numerical values for display"""
    if value is None:
        return "N/A"
    return f"{float(value):.2f}"

def show_prizes():
    """Display all prizes in the system"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Get all prizes ordered by ID
            prizes = Prize.query.order_by(Prize.id).all()
            
            if not prizes:
                print("\nNo prizes found in the system.")
                return
            
            # Prepare data for tabulation
            prize_data = []
            for prize in prizes:
                prize_data.append([
                    prize.id,
                    prize.name,
                    prize.description or "N/A",
                    prize.type,
                    prize.custom_type or "N/A",
                    prize.tier,
                    prize.tier_priority,
                    format_value(prize.retail_value),
                    format_value(prize.cash_value),
                    format_value(prize.credit_value),
                    prize.total_quantity or "Unlimited",
                    prize.available_quantity or "N/A",
                    prize.min_threshold,
                    prize.total_won,
                    prize.total_claimed,
                    prize.win_limit_per_user or "None",
                    prize.win_limit_period_days or "None",
                    prize.status,
                    format_datetime(prize.created_at),
                    format_datetime(prize.updated_at),
                    prize.created_by_id
                ])
            
            # Define headers
            headers = [
                "ID", "Name", "Description", "Type", "Custom Type", "Tier", 
                "Tier Priority", "Retail Value", "Cash Value", "Credit Value",
                "Total Qty", "Available Qty", "Min Threshold", "Total Won",
                "Total Claimed", "Win Limit/User", "Win Period(Days)", "Status",
                "Created At", "Updated At", "Created By"
            ]
            
            # Print the table
            print("\nSystem Prizes:")
            print(tabulate(
                prize_data,
                headers=headers,
                tablefmt="grid",
                numalign="right",
                stralign="left"
            ))
            
            # Print summary
            print(f"\nTotal Prizes: {len(prizes)}")
            status_summary = {}
            for prize in prizes:
                status_summary[prize.status] = status_summary.get(prize.status, 0) + 1
            
            print("\nStatus Summary:")
            for status, count in status_summary.items():
                print(f"{status}: {count}")
            
        except Exception as e:
            print(f"Error displaying prizes: {str(e)}")

if __name__ == "__main__":
    show_prizes()