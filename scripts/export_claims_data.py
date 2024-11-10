# scripts/export_claims_data.py

from pathlib import Path
import sys
from datetime import datetime
import pandas as pd
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from src.shared import db
from src.shared.config import config
from src.prize_service.models import PrizeAllocation, ClaimStatus
from src.user_service.models import User
import logging

logger = logging.getLogger(__name__)

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

def export_claims():
    """Export claims data to CSV files"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Ensure export directory exists
            export_dir = project_root / 'data' / 'exports'
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all allocations with simpler query
            allocations = db.session.query(PrizeAllocation)\
                .order_by(PrizeAllocation.created_at.desc())\
                .all()

            if not allocations:
                print("No claims found to export.")
                return None, None
            
            # Prepare claims data
            claim_data = []
            for alloc in allocations:
                # Access relationships through backref
                prize = alloc.prize
                pool = alloc.pool
                user = db.session.get(User, alloc.winner_user_id) if alloc.winner_user_id else None
                
                claim_data.append({
                    'Allocation ID': alloc.id,
                    'Prize Name': prize.name if prize else 'Unknown',
                    'Prize Type': prize.type if prize else 'Unknown',
                    'Pool Name': pool.name if pool else 'Unknown',
                    'Winner Username': user.username if user else 'Unknown',
                    'Winner Email': user.email if user else 'Unknown',
                    'Claim Status': alloc.claim_status,
                    'Won At': format_datetime(alloc.won_at),
                    'Claimed At': format_datetime(alloc.claimed_at),
                    'Claim Deadline': format_datetime(alloc.claim_deadline),
                    'Original Value': format_value(alloc.original_value),
                    'Value Claimed': format_value(alloc.value_claimed),
                    'Reference Type': alloc.reference_type,
                    'Reference ID': alloc.reference_id,
                    'Created At': format_datetime(alloc.created_at),
                    'Updated At': format_datetime(alloc.updated_at)
                })

            # Create DataFrame and export
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/exports/prize_claims_{timestamp}.csv'
            
            df = pd.DataFrame(claim_data)
            df.to_csv(filename, index=False)
            
            # Generate summary
            summary_data = [
                {'Metric': 'Report Generated', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Metric': 'Total Claims', 'Value': len(claim_data)},
                {'Metric': 'Pending Claims', 'Value': sum(1 for x in claim_data if x['Claim Status'] == ClaimStatus.PENDING.value)},
                {'Metric': 'Claimed', 'Value': sum(1 for x in claim_data if x['Claim Status'] == ClaimStatus.CLAIMED.value)},
                {'Metric': 'Expired', 'Value': sum(1 for x in claim_data if x['Claim Status'] == ClaimStatus.EXPIRED.value)},
                {'Metric': 'Total Value Claimed', 'Value': sum(x['Value Claimed'] for x in claim_data if x['Value Claimed'])},
            ]
            
            summary_filename = f'data/exports/prize_claims_summary_{timestamp}.csv'
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(summary_filename, index=False)
            
            print(f"Claims data exported to: {filename}")
            print(f"Summary report exported to: {summary_filename}")
            return filename, summary_filename
            
        except Exception as e:
            print(f"Error during export: {str(e)}")
            logger.error(f"Export error: {str(e)}", exc_info=True)
            return None, None

def export_expired_claims():
    """Export expired claims for analysis"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        try:
            # Query expired claims directly
            expired_allocations = PrizeAllocation.query\
                .filter_by(claim_status=ClaimStatus.EXPIRED.value)\
                .order_by(PrizeAllocation.created_at.desc())\
                .all()

            if not expired_allocations:
                print("No expired claims found.")
                return None

            # Prepare expired claims data
            expired_data = []
            for alloc in expired_allocations:
                prize = alloc.prize
                user = db.session.get(User, alloc.winner_user_id) if alloc.winner_user_id else None
                
                expired_data.append({
                    'Allocation ID': alloc.id,
                    'Prize Name': prize.name if prize else 'Unknown',
                    'Prize Type': prize.type if prize else 'Unknown',
                    'Winner Username': user.username if user else 'Unknown',
                    'Winner Email': user.email if user else 'Unknown',
                    'Won At': format_datetime(alloc.won_at),
                    'Claim Deadline': format_datetime(alloc.claim_deadline),
                    'Original Value': format_value(alloc.original_value),
                    'Reference Type': alloc.reference_type,
                    'Reference ID': alloc.reference_id,
                    'Days Until Expired': (alloc.claim_deadline - alloc.won_at).days if alloc.claim_deadline and alloc.won_at else None
                })

            # Export expired claims
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/exports/expired_claims_{timestamp}.csv'
            
            df = pd.DataFrame(expired_data)
            df.to_csv(filename, index=False)
            
            print(f"Expired claims data exported to: {filename}")
            return filename

        except Exception as e:
            print(f"Error exporting expired claims: {str(e)}")
            logger.error(f"Export error: {str(e)}", exc_info=True)
            return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export prize claims data')
    parser.add_argument('--expired', action='store_true', 
                      help='Export only expired claims')
    args = parser.parse_args()
    
    if args.expired:
        export_expired_claims()
    else:
        export_claims()