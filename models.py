from app import db
from enum import Enum
import datetime
import bcrypt


""" Creating tables to be used by database. They include:
    tags: many-to-many table between club and tag
"""
clubs2tags = db.Table('clubs2tags',
                db.Column('tag_id', db.String, db.ForeignKey('tag.name')),
                db.Column('club_id', db.String(100), db.ForeignKey('club.code')))

favorites = db.Table('favorites',
                db.Column('club_id', db.String(100), db.ForeignKey('club.code')),
                db.Column('user_id', db.String, db.ForeignKey('user.email')))

class Club (db.Model):
    """
    required inputs: code, name
    optional inputs: description, tags
    """
    code = db.Column("code", db.String(100), nullable=False, primary_key = True)
    name = db.Column("name", db.String(100), nullable=False)
    description = db.Column("description", db.String, nullable=True)

    # we define relationships in club for many-to-many tables
    # to concentrate logic here
    tags = db.relationship('Tag', secondary=clubs2tags,
                                    backref=db.backref('clubs', lazy='dynamic'))
    favorites = db.relationship('User', secondary=favorites,
                                    backref=db.backref('favorites', lazy='dynamic'))

    def __init__(self, code, name, description="", tags=[], fav_cnt=0):
        self.code = code.lower()
        self.name = name
        self.description = description
        self.fav_cnt = fav_cnt


class Tag (db.Model) :
    name = db.Column(db.String, nullable=False, primary_key=True, unique=True)

    def __init__(self, name):
        self.name = name.lower()


class User (db.Model):
    # using emails as primary key because...
    email = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String, unique=False, nullable=False)
    session_key = db.Column(db.String(20), nullable=True)
    session_expiration = db.Column(db.DateTime, nullable=True)


    def __init__ (self, email, username, pw_plain, session_key=None,
                                session_expiration =None) :
        self.email = email
        self.username = username
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(pw_plain.encode('utf-8'), salt)
        self.session_key = session_key
        #session_expiration must be in the format of datetime strftime return
        self.session_expiration = None if session_expiration is None \
                                        else datetime.strptime(session_expiration)


# Your database models should go here.
# Check out the Flask-SQLAlchemy quickstart for some good docs!
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/

