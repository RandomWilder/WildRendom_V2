# scripts/export_prize_data.py

from pathlib import Path
import sys
import csv
from datetime import datetime
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config
from src.prize_service.models import (
    Prize, PrizePool, PrizePoolAllocation,
    PoolStatus, AllocationStrategy
)

def format_datetime(dt):
    """Format datetime for CSV"""
    if not dt:
        return ""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_value(value):
    """Format numerical values for CSV"""
    if value is None:
        return ""
    return float(value)

def export_prizes():
    """Export prizes to CSV"""
    prizes = Prize.query.order_by(Prize.id).all()
    
    if not prizes:
        print("No prizes found to export.")
        return
    
    # Prepare data for DataFrame
    prize_data = []
    for prize in prizes:
        prize_data.append({
            'ID': prize.id,
            'Name': prize.name,
            'Description': prize.description or '',
            'Type': prize.type,
            'Custom Type': prize.custom_type or '',
            'Tier': prize.tier,
            'Tier Priority': prize.tier_priority,
            'Retail Value': format_value(prize.retail_value),
            'Cash Value': format_value(prize.cash_value),
            'Credit Value': format_value(prize.credit_value),
            'Total Quantity': prize.total_quantity or 'Unlimited',
            'Available Quantity': prize.available_quantity or '',
            'Min Threshold': prize.min_threshold,
            'Total Won': prize.total_won,
            'Total Claimed': prize.total_claimed,
            'Win Limit Per User': prize.win_limit_per_user or '',
            'Win Period (Days)': prize.win_limit_period_days or '',
            'Status': prize.status,
            'Created At': format_datetime(prize.created_at),
            'Updated At': format_datetime(prize.updated_at),
            'Created By ID': prize.created_by_id
        })
    
    # Create DataFrame and export
    df = pd.DataFrame(prize_data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'data/exports/prizes_{timestamp}.csv'
    df.to_csv(filename, index=False)
    return filename

def export_prize_pools():
    """Export prize pools and allocations to separate CSVs"""
    pools = PrizePool.query.order_by(PrizePool.id).all()
    
    if not pools:
        print("No prize pools found to export.")
        return
    
    # Prepare pools data
    pool_data = []
    allocation_data = []
    
    for pool in pools:
        # Pool information
        pool_data.append({
            'Pool ID': pool.id,
            'Name': pool.name,
            'Description': pool.description or '',
            'Status': pool.status,
            'Strategy': pool.allocation_strategy,
            'Start Date': format_datetime(pool.start_date),
            'End Date': format_datetime(pool.end_date),
            'Budget Limit': format_value(pool.budget_limit),
            'Current Allocation': format_value(pool.current_allocation),
            'Total Value': format_value(pool.total_value),
            'Created At': format_datetime(pool.created_at),
            'Updated At': format_datetime(pool.updated_at),
            'Created By ID': pool.created_by_id
        })
        
        # Pool allocations
        try:
            allocations = PrizePoolAllocation.query.filter_by(pool_id=pool.id).all()
            for alloc in allocations:
                # Get prize information directly from the database
                prize = Prize.query.get(alloc.prize_id)
                prize_name = prize.name if prize else 'Unknown Prize'
                
                allocation_data.append({
                    'Pool ID': pool.id,
                    'Prize ID': alloc.prize_id,
                    'Prize Name': prize_name,
                    'Quantity Allocated': alloc.quantity_allocated,
                    'Quantity Remaining': alloc.quantity_remaining,
                    'Allocation Rules': str(alloc.allocation_rules) if alloc.allocation_rules else ''
                })
        except Exception as e:
            print(f"Warning: Error processing allocations for pool {pool.id}: {str(e)}")
            continue
    
    # Create DataFrames and export
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export pools
    pools_df = pd.DataFrame(pool_data)
    pools_filename = f'data/exports/prize_pools_{timestamp}.csv'
    pools_df.to_csv(pools_filename, index=False)
    
    # Export allocations
    if allocation_data:
        allocations_df = pd.DataFrame(allocation_data)
        allocations_filename = f'data/exports/pool_allocations_{timestamp}.csv'
        allocations_df.to_csv(allocations_filename, index=False)
        return pools_filename, allocations_filename
    
    return pools_filename, None

def ensure_export_directory():
    """Ensure the exports directory exists"""
    export_dir = project_root / 'data' / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir

def export_all():
    """Export all prize-related data to CSV files"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Ensure export directory exists
            ensure_export_directory()
            
            # Export prizes
            prizes_file = export_prizes()
            if prizes_file:
                print(f"Prizes exported to: {prizes_file}")
            
            # Export pools and allocations
            pools_file, alloc_file = export_prize_pools()
            if pools_file:
                print(f"Prize pools exported to: {pools_file}")
            if alloc_file:
                print(f"Pool allocations exported to: {alloc_file}")
            
            print("\nExport completed successfully!")
            
        except Exception as e:
            print(f"Error during export: {str(e)}")
            raise  # Add this to see full traceback

if __name__ == "__main__":
    export_all()