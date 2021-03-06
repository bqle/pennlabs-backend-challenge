import os
import json
from app import DB_FILE
from models import *
import random

session_key = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefjhiklmnopqrstuvwxyz')
                      for i in range(30))
def create_user():
    josh = User(email="josh@upenn.edu", username="josh", pw_plain="joshiscool")
    # also logs josh in for testing purposes
    josh.session_key = session_key
    josh.session_expiration = datetime.datetime.now() + datetime.timedelta(hours=24)
    db.session.add(josh)

    # for login testing
    andy = User(email="andy@upenn.edu", username="andy", pw_plain="andyiscool")
    db.session.add(andy)

def load_data():
    print("Loading data into db...")
    clubs_file = open("clubs.json")
    clubs_data = clubs_file.read()
    clubs_file.close()
    clubs_list = json.loads(clubs_data)
    # dictionary containing tag string and tag objects
    all_tags = {}

    for club in clubs_list :
        club_obj = Club(code=club['code'],
                        name=club['name'],
                        description=club['description'])
        # removing duplicate tags
        club['tags'] = list(set(club['tags']))
        for tag in club['tags'] :
            if (tag not in all_tags) :
                tag_obj = Tag(name=tag.lower())
                all_tags[tag] = tag_obj
            club_obj.tags.append(all_tags[tag])

        db.session.add(club_obj)

    db.session.commit()
    print("Finished loading data.")

# No need to modify the below code.
if __name__ == '__main__':
    # Delete any existing database before bootstrapping a new one.
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    db.create_all()
    create_user()
    load_data()
