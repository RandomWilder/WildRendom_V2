# scripts/safe_migrate.py
import logging
from pathlib import Path
import sys
from flask import Flask
from flask_migrate import Migrate
import sqlalchemy as sa
from sqlalchemy import inspect

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SafeMigration:
    def __init__(self, app_name: str, target_table: str = None):
        self.app_name = app_name
        self.target_table = target_table
        self.backup_file = None
        self.project_root = Path(__file__).parent.parent
        
    def create_app(self):
        """Create Flask app with database configuration"""
        app = Flask(self.app_name)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.project_root}/data/wildrandom.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

    def backup_table(self, table_name: str):
        """Create backup of specific table"""
        logger.info(f"Creating backup of table: {table_name}")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_file = f"backup_{table_name}_{timestamp}.sql"
        
        with self.engine.connect() as conn:
            # Get table structure and data
            table_info = inspect(self.engine).get_columns(table_name)
            data = conn.execute(f"SELECT * FROM {table_name}").fetchall()
            
            # Write backup
            with open(self.backup_file, 'w') as f:
                # Write create table
                cols = [f"{col['name']} {col['type']}" for col in table_info]
                f.write(f"CREATE TABLE {table_name} (\n  {','.join(cols)}\n);\n")
                
                # Write data
                for row in data:
                    f.write(f"INSERT INTO {table_name} VALUES {row};\n")
        
        logger.info(f"Backup created: {self.backup_file}")

    def verify_migration(self, migration_script: str) -> bool:
        """Verify migration script safety"""
        logger.info("Verifying migration safety...")
        
        with open(migration_script, 'r') as f:
            content = f.read().lower()
            
            # Check for dangerous operations
            dangerous_ops = ['drop table', 'drop database', 'delete from']
            for op in dangerous_ops:
                if op in content and not f"drop table if exists {self.target_table}" in content:
                    logger.error(f"Dangerous operation detected: {op}")
                    return False
            
            # Verify target table
            if self.target_table and self.target_table not in content:
                logger.error(f"Migration doesn't target specified table: {self.target_table}")
                return False
        
        return True

    def run_migration(self, migration_script: str):
        """Run migration with safety checks"""
        try:
            # Verify migration first
            if not self.verify_migration(migration_script):
                logger.error("Migration verification failed!")
                return False

            # Create backup
            if self.target_table:
                self.backup_table(self.target_table)

            # Run migration
            logger.info("Running migration...")
            app = self.create_app()
            migrate = Migrate(app, db)
            
            with app.app_context():
                # Execute migration
                with open(migration_script, 'r') as f:
                    exec(f.read())
                
            logger.info("Migration completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            if self.backup_file:
                logger.info(f"Backup available at: {self.backup_file}")
            return False

    @staticmethod
    def list_tables():
        """List all database tables"""
        app = create_app()
        with app.app_context():
            inspector = inspect(db.engine)
            return inspector.get_table_names()