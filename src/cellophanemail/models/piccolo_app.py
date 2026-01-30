"""Piccolo app configuration for CellophoneMail models."""

from piccolo.apps.migrations.auto import MigrationManager
from piccolo.conf.apps import AppConfig

from .user import User
from .organization import Organization
from .email_log import EmailLog
from .subscription import Subscription
from .shield_address import ShieldAddress
from .message_analysis import MessageAnalysis
from .sender_summary import SenderSummary
from .analysis_job import AnalysisJob

APP_CONFIG = AppConfig(
    app_name="cellophanemail",
    migrations_folder_path="src/cellophanemail/models/migrations",
    table_classes=[
        Organization,
        User,
        EmailLog,
        Subscription,
        ShieldAddress,
        MessageAnalysis,
        SenderSummary,
        AnalysisJob,
    ],
    migration_dependencies=[],
    commands=[MigrationManager],
)