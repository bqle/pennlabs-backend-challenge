import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import werkzeug
import bcrypt
import random

DB_FILE = "clubreview.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"
db = SQLAlchemy(app)


@app.route('/')
def main():
    return "Welcome to Penn Club Review!"

@app.route('/api')
def api():
    return jsonify({"message": "Welcome to the Penn Club Review API!."})

@app.route('/api/clubs', methods=['GET'])
def get_all_clubs():
    from models import Club, User
    club_names = [{'code': club.code,
                   'name': club.name,
                   'fav_cnt': db.session.query(User).with_parent(
                       club, "favorites").count()} for club in Club.query.all()]
    return jsonify(club_names)

@app.route('/api/clubs/search', methods=['GET'])
def search_clubs_with_string():
    from models import Club, Tag, User
    search_string = request.args.get('string')
    # ilike is case insensitive
    clubs_with_string = Club.query.filter(Club.name.ilike("%"+search_string+"%")).all()
    clubs_json_ready = [{'code': club.code,
                        'name': club.name,
                        'description': club.description,
                        'tags': [tag.name for tag in db.session.query(Tag).with_parent(
                                    club, "tags")],
                        'fav_cnt': db.session.query(User).with_parent(
                            club, "favorites").count()} for club in clubs_with_string]
    return jsonify(clubs_json_ready)

@app.route('/api/clubs/favorite_users', methods=['GET'])
def get_favorite_users_of_club():
    from models import Club, User
    # can get access with either club code or name
    code = request.args.get('code')
    name = request.args.get('name')
    if (code is None and name is None) :
        return "missing both club code and name", 406

    club = db.session.query(Club).filter((Club.code==code) | (Club.name==name)).first()
    if (club is None) :
        return "club doesn't exist", 404
    else :
        users = [{
            'email': user.email,
            'username': user.username,
        }
            for user in db.session.query(User).with_parent(
                club, "favorites").all()
        ]
        return jsonify(users), 200


@app.route('/api/clubs/create', methods=['POST'])
@app.errorhandler(werkzeug.exceptions.BadRequest)
def add_club() :
    from models import Club, Tag
    # turn post body into json
    data = json.loads(request.get_data())
    if not authenticate_post(data) :
        return "permission denied", 404

    if (('code' not in data) or ('name' not in data)) :
        return "missing club code or name", 406

    # club with the same code or name already exist
    if (Club.query.filter((Club.code==data['code']) | (Club.name==data['name'])).count() > 0) :
        return "a club with the same name or code already exists", 406

    club_obj = Club(code=data['code'].lower(),
                    name=data['name'],
                    description=data['description'] if ('description' in data) else ""
                    )
    if ('tags' in data) :
        # removing duplicate tags
        data['tags'] = list(set(data['tags']))

        for tag in data['tags'] :
            add_tag_to_club(club_obj, tag)

    db.session.add(club_obj)
    db.session.commit()
    return "successfully added club " + data['name'], 200

@app.route('/api/clubs/modify', methods=['POST'])
def modify_club() :
    """
    Can change all values except favorite count
    Limitation: club code because it is the db's primary key
                and name must not cause conflict with existing clubs
    """
    from models import Club, Tag
    data = json.loads(request.get_data())
    if not authenticate_post(data) :
        return "permission denied", 404

    # if post body does not have the right structure (described in documentation), error
    if (('code' not in data) or ('name' not in data) or ('new_data' not in data)):
        return "missing information", 406

    code = data['code']
    old_name = data['name']
    # if code and name are not correctly paired or do not exist, we raise an error
    if ((Club.query.filter_by(code=code).count() == 0) or
        (Club.query.filter_by(code=code).first().name != old_name)) :
        return "invalid code name pair", 406

    new_data = data['new_data']
    new_name = new_data['name']
    target_club = Club.query.filter_by(code=code).first()

    # if we are changing club name and the new name conflicts, we raise an error
    if (('name' in new_data) and (new_name != old_name) and
            (Club.query.filter_by(name=new_name).count() > 0)):
        return "new name causes conflict", 406

    # valid modifications are done below
    for key, value in new_data.items():
        if (key == 'name'):
            target_club.name = value
        elif (key == 'description'):
            target_club.description = value
        elif (key == 'tags'):
            # removing duplicate tags
            new_data['tags'] = list(set(new_data['tags']))

            for tag in new_data['tags']:
                add_tag_to_club(target_club, tag)

    db.session.commit()
    return "successfully updated club with code: " + code, 200

@app.route('/api/clubs/delete', methods=['POST'])
def delete_club() :
    # can only delete by club code
    from models import Club, Tag
    # turn post body into json
    data = json.loads(request.get_data())
    if not authenticate_post(data) :
        return "permission denied", 404

    if (('code' not in data)) :
        return "missing club code", 406

    db.session.query(Club).filter_by(code=data['code']).delete()
    db.session.commit()
    return "successfully removed club", 200

# stream line the process of adding club-tag relationship
def add_tag_to_club (club, tag_name):
    from models import Tag, Club
    tag_placeholder = db.session.query(Tag).filter_by(name=tag_name).first();
    if (tag_placeholder is None) : #tag does not yet exist
        print("tag does not exist:" + tag_name)
        new_tag = Tag(name=tag_name)
        db.session.add(new_tag)
        club.tags.append(new_tag)
    else : # tag does exist
        print("tag does exist" + tag_placeholder.name)
        club.tags.append(tag_placeholder)

@app.route('/api/user/favoriting', methods=['POST'])
def favoriting() :
    from models import User, Club

    data = json.loads(request.get_data())
    if not authenticate_post(data) :
        return "permission denied", 404

    # error if post body does not have the right structure (described in documentation)
    if (('email' not in data) or ('club' not in data)):
        return "missing information", 406

    print(data['club'])
    print(data['email'])

    club_placeholder = Club.query.filter_by(code=data['club']).first()
    user_placeholder = User.query.filter_by(email=data['email']).first()

    if ( club_placeholder is None or user_placeholder is None):
        return "invalid email or club code", 406

    # creating relationship
    if (user_placeholder not in club_placeholder.favorites) :
        club_placeholder.favorites.append(user_placeholder)
        db.session.commit()
    return user_placeholder.username + " successfully favorited club " + data['club'], 200

@app.route('/api/user', methods=['GET'])
def get_user_with_username():
    from models import User
    username = request.args.get('username')
    query_result = User.query.filter_by(username=username)

    if query_result.count() == 0 :
        return "user doesn't exist", 404

    user = query_result.first()
    # revealing only safe information
    truncated_user = {
        'email': user.email,
        'username': user.username,
    }
    return jsonify(truncated_user), 200

@app.route('/api/user/favorite_clubs', methods=['GET'])
def get_user_favorite_clubs():
    from models import User, Club, Tag

    # can get access with either username or email
    username = request.args.get('username')
    email = request.args.get('email')
    if (username is None and email is None) :
        return "missing both username and email", 406

    user = db.session.query(User).filter((User.email==email) | (User.username==username)).first()
    if (user is None) :
        return "user doesn't exist", 404
    else :
        clubs = [{
            'code': club.code,
            'name': club.name,
            'description': club.description,
            'tags': [tag.name for tag in db.session.query(Tag).with_parent(
                club, "tags")]
            }
            for club in db.session.query(Club).with_parent(
                        user, "favorites").all()
        ]
        return jsonify(clubs), 200

@app.route('/api/user/login', methods=['POST'])
def login():
    from models import User
    data = json.loads(request.get_data())

    if ('email' not in data or 'password' not in data) :
        return "missing email or password", 406

    email = data['email']
    password = data['password'].encode('utf-8')
    user_placeholder = db.session.query(User).filter_by(email=email).first()
    if (user_placeholder is None) :
        return "a user with that email does not exist", 406

    salt = bcrypt.gensalt()
    if bcrypt.checkpw(password, user_placeholder.password_hash) :
        # if successful, we return with a session key
        session_key = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPabcdefjhiklmnop')
                              for i in range(20))
        now = datetime.datetime.now()
        # session_key expires in 24 hours
        session_expiration = now + datetime.timedelta(hours=24)
        user_placeholder.session_key = session_key
        user_placeholder.session_expiration = session_expiration
        db.session.commit()
        key_data = {
            'session_key': session_key
        }
        return jsonify(key_data), 200
    else :
        return "password does not match", 406

@app.route('/api/user/signup', methods=['POST'])
def signup():
    from models import User
    data = json.loads(request.get_data())
    if ('email' not in data or 'password' not in data or
        'username' not in data) :
        return "missing email, password, or username", 406

    email = data['email']
    username = data['username']
    password = data['password']

    user_by_email = db.session.query(User).filter_by(email=email).first()
    user_by_username = db.session.query(User).filter_by(username=username).first()
    if user_by_email is not None or user_by_username is not None:
        return "a user with that email or username already exist", 406

    new_user = User(email=data['email'], username=data['username'], pw_plain=data['password'])
    session_key = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPabcdefjhiklmnop')
                          for i in range(20))
    # session_key expires in 24 hours
    session_expiration = datetime.datetime.now() + datetime.timedelta(hours=24)
    new_user.session_key = session_key
    new_user.session_expiration = session_expiration
    db.session.add(new_user)
    db.session.commit()

    key_data = {
        'session_key': session_key
    }
    return jsonify(key_data), 200

@app.route('/api/user/logout', methods=['POST'])
def logout():
    from models import User
    # turn post body into json
    data = json.loads(request.get_data())
    if not authenticate_post(data) :
        return "permission denied", 404

    email = data['email']
    user_placeholder = db.session.query(User).filter_by(email=email).first()
    user_placeholder.session_key = None
    user_placeholder.session_expiration = None
    db.session.commit()
    return "succesfully logged out", 200

# authenticate request for all post except login and signup
def authenticate_post (data) :
    from models import User
    if ('session_key' not in data):
        return False

    session_key = data['session_key']
    user_placeholder = db.session.query(User).filter_by(session_key=session_key).first()

    return (user_placeholder is not None) and \
           (user_placeholder.session_key is not None) and \
           (user_placeholder.session_expiration is not None) and\
           (datetime.datetime.now() < user_placeholder.session_expiration)


@app.route('/api/tag', methods=['GET'])
def get_all_tags_and_count() :
    from models import Tag, Club
    tags_and_cnt = [{'name': tag.name,
                   'cnt' : db.session.query(Club).with_parent(
                            tag, "clubs").count()
                   } for tag in Tag.query.all()]
    return jsonify(tags_and_cnt)

if __name__ == '__main__':
    app.run()
