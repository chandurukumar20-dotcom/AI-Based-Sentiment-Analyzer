# routes module
from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__)
analysis_bp = Blueprint("analysis", __name__)
history_bp = Blueprint("history", __name__)

from . import dashboard, analysis, history
