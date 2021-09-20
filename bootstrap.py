import os
import json
from app import DB_FILE
from models import *

def create_user():
    josh = User(email="josh@upenn.edu", username="josh", pw_plain="joshiscool")
    db.session.add(josh)


def load_data():
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
                tag_obj = Tag(name=tag)
                all_tags[tag] = tag_obj
            club_obj.tags.append(all_tags[tag])

        db.session.add(club_obj)
        print("added club " + club['name'])

    db.session.commit()

# No need to modify the below code.
if __name__ == '__main__':
    # Delete any existing database before bootstrapping a new one.
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    db.create_all()
    create_user()
    load_data()
