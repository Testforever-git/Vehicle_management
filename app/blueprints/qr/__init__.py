from flask import Blueprint

bp = Blueprint("qr", __name__)
from . import routes  # noqa
