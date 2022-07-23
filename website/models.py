from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    country = db.Column(db.String(150))
    age = db.Column(db.Integer)
    position = db.Column(db.String(150))
    market_value = db.Column(db.Integer)
    is_on_sale = db.Column(db.Boolean)
    selling_price = db.Column(db.Integer)

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))  # M-1 relation to Team


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    country = db.Column(db.String(150))
    cash_available = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 1-1 relation to User
    players = db.relationship('Player')  # 1-M relation with Player


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    username = db.Column(db.String(150), unique=True)
    signup_date = db.Column(db.DateTime(timezone=True), default=func.now())

    team = db.relationship('Team')  # 1-1 relationship with Team
