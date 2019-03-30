from flask import Blueprint

passport_blue = Blueprint('passport_blue', __name__, url_prefix='/passport')

from . import views
