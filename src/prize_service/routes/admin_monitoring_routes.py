# src/prize_service/routes/admin_monitoring_routes.py

import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from src.shared.auth import admin_required
from src.prize_service.services.monitoring_service import PrizeMonitoringService
from src.prize_service.services.admin_monitoring_service import PrizeAdminMonitoringService

monitoring_bp = Blueprint('prize_monitoring', __name__)
logger = logging.getLogger(__name__)

@monitoring_bp.route('/pools/<int:pool_id>/health', methods=['GET'])
@admin_required
def get_pool_health(pool_id):
    """Get comprehensive pool health metrics"""
    try:
        health_data, error = PrizeMonitoringService.get_pool_health(pool_id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(health_data)
    except Exception as e:
        logger.error(f"Error getting pool health: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/pools/<int:pool_id>/audit', methods=['GET'])
@admin_required
def get_pool_audit(pool_id):
    """Get complete audit trail for pool"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        audit_data, error = PrizeMonitoringService.get_pool_audit(
            pool_id=pool_id,
            start_date=start_date,
            end_date=end_date
        )
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(audit_data)
    except Exception as e:
        logger.error(f"Error getting pool audit: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/system', methods=['GET'])
@admin_required
def get_system_metrics():
    """Get system-wide monitoring metrics"""
    try:
        metrics, error = PrizeAdminMonitoringService.get_system_metrics()
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/performance', methods=['GET'])
@admin_required
def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        metrics, error = PrizeAdminMonitoringService.get_performance_metrics()
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/pools/<int:pool_id>/alerts', methods=['GET'])
@admin_required
def get_pool_alerts(pool_id):
    """Get active alerts for pool"""
    try:
        alerts, error = PrizeMonitoringService.get_pool_alerts(pool_id)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error getting pool alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500
    