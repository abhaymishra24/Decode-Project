

# write code for basic fetures of debate website using python and flask

# write apis for user registration, login, creating debates, viewing debates, and voting on debates

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask_cors import CORS
import os
import jwt
from functools import wraps
from datetime import datetime, timedelta
import uuid 
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///debate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False        
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    debates = db.relationship('Debate', backref='creator', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
    
    
class Debate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    votes = db.relationship('Vote', backref='debate', lazy=True)
    attachment = db.Column(db.String(100), nullable=True)
    
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    debate_id = db.Column(db.Integer, db.ForeignKey('debate.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote_type = db.Column(db.String(10))  # 'upvote' or 'downvote'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4()), username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'})

@app.route('/login', methods=['POST'])

def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401
    token = jwt.encode({'public_id': user.public_id, 'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']}, app.config['JWT_SECRET_KEY'], algorithm="HS256")
    return jsonify({'token': token})

@app.route('/debates', methods=['POST'])
@token_required
def create_debate(current_user):
    title = request.form.get('title')
    description = request.form.get('description')
    file = request.files.get('attachment')
    filename = None
    if file and allowed_file(file.filename):
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    new_debate = Debate(title=title, description=description, user_id=current_user.id, attachment=filename)
    db.session.add(new_debate)
    db.session.commit()
    return jsonify({'message': 'Debate created successfully!'})
@app.route('/debates', methods=['GET'])
def get_debates():
    debates = Debate.query.all()
    output = []
    for debate in debates:
        debate_data = {
            'id': debate.id,
            'title': debate.title,
            'description': debate.description,
            'created_at': debate.created_at,
            'creator': debate.creator.username,
            'attachment': debate.attachment
        }
        output.append(debate_data)
    return jsonify({'debates': output})
@app.route('/debates/<int:debate_id>/vote', methods=['POST'])
@token_required
def vote_debate(current_user, debate_id):
    data = request.get_json()
    debate = Debate.query.get_or_404(debate_id)
    existing_vote = Vote.query.filter_by(debate_id=debate.id, user_id=current_user.id).first()
    if existing_vote:
        return jsonify({'message': 'You have already voted on this debate!'}), 400
    if data['vote_type'] not in ['upvote', 'downvote']:
        return jsonify({'message': 'Invalid vote type!'}), 400
    new_vote = Vote(debate_id=debate.id, user_id=current_user.id, vote_type=data['vote_type'])
    db.session.add(new_vote)
    db.session.commit()
    return jsonify({'message': 'Vote recorded successfully!'})