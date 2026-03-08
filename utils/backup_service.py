import shutil
import datetime
from pathlib import Path
from utils.logger import app_logger

class BackupService:
    @staticmethod
    def create_database_backup():
        """Creates a timestamped copy of the database file."""
        try:
            root_dir = Path(__file__).parent.parent
            db_file = root_dir / "stock_management.db"
            
            if not db_file.exists():
                app_logger.warning("Database file not found for backup.")
                return False
                
            backup_dir = root_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # Clean up old backups (keep last 7)
            BackupService._cleanup_old_backups(backup_dir)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"stock_management_{timestamp}.db"
            backup_target = backup_dir / backup_filename
            
            shutil.copy2(db_file, backup_target)
            app_logger.info(f"Successfully created database backup: {backup_filename}")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to create database backup: {str(e)}")
            return False
            
    @staticmethod
    def _cleanup_old_backups(backup_dir: Path, max_backups: int = 7):
        """Keeps only the most recent 'max_backups' files in the directory."""
        try:
            backups = list(backup_dir.glob("stock_management_*.db"))
            if len(backups) > max_backups:
                # Sort by modification time (oldest first)
                backups.sort(key=lambda x: x.stat().st_mtime)
                
                # Delete the oldest files
                files_to_delete = len(backups) - max_backups
                for i in range(files_to_delete):
                    backups[i].unlink()
                    app_logger.info(f"Deleted old backup: {backups[i].name}")
        except Exception as e:
            app_logger.error(f"Failed to clean up old backups: {str(e)}")
