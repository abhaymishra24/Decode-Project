
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

@app.route('/debates', methods=['POST'])
@token_required
def create_debate(current_user):
    data = request.form
    title = data.get('title')
    description = data.get('description')
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        new_debate = Debate(title=title, description=description, file_path=unique_filename, creator_id=current_user.id)
        db.session.add(new_debate)
        db.session.commit()
        return jsonify({'message': 'New debate created!'}), 201
    else:
        return jsonify({'message': 'File type not allowed'}), 400   
    
@app.route('/debates', methods=['GET'])
def get_debates():
    debates = Debate.query.all()
    output = []
    for debate in debates:
        debate_data = {}
        debate_data['id'] = debate.id
        debate_data['title'] = debate.title
        debate_data['description'] = debate.description
        debate_data['file_path'] = debate.file_path
        debate_data['creator'] = User.query.get(debate.creator_id).username
        debate_data['created_at'] = debate.created_at
        debate_data['upvotes'] = Vote.query.filter_by(debate_id=debate.id, vote_type='upvote').count()
        debate_data['downvotes'] = Vote.query.filter_by(debate_id=debate.id, vote_type='downvote').count()
        output.append(debate_data)
    return jsonify({'debates': output})

