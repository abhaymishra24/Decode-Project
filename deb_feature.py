
# here write code for debate features like creating debates, viewing debates, voting on debates

from main import db, app, token_required, allowed_file
from flask import request, jsonify
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
from sqlalchemy import func
from main import User
from main import Debate, Vote
from main import ALLOWED_EXTENSIONS
from main import UPLOAD_FOLDER
from main import ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from main import Debate, Vote
from main import db
from main import User
id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    votes = db.relationship('Vote', backref='debate', lazy=True)
    attachment = db.Column(db.String(200), nullable=True)
    