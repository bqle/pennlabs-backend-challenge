import unittest
import json
import bootstrap
from bootstrap import session_key
from app import app, db, DB_FILE
from models import User, Club, Tag

TEST_DB = 'clubreview.db'

class BasicTests(unittest.TestCase):
    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE}"

        self.app = app.test_client()
        db.drop_all()
        db.create_all()
        bootstrap.create_user()
        bootstrap.load_data()

        print(session_key)
        # Disable sending emails during unit testing
        self.assertEqual(app.debug, False)

    # executed after each test
    def tearDown(self):
        pass

    ###############
    #### tests ####
    ###############
    def test_main_page(self):
        print("\n Testing /")
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_api(self):
        print("\n Testing /api")
        response = self.app.get('/api')
        self.assertEqual(response.status_code, 200)

    def test_clubs_all(self):
        print("\n Testing /api/clubs/")
        response = self.app.get('/api/clubs')
        data = json.loads(response.data)

        assert len(data) == 5

    def test_clubs_search(self):
        print("\n Testing /api/clubs/search")
        response = self.app.get('/api/clubs/search?string=penn')
        data = json.loads(response.data)
        assert len(data) == 4

    def test_clubs_favorite_users(self):
        print("\n Testing /api/clubs/favorite_users valid")
        josh = User.query.filter_by(email='josh@upenn.edu').first()
        pppjo_club = Club.query.filter_by(code='pppjo').first()
        pppjo_club.favorites.append(josh)
        db.session.commit()

        response = self.app.get('/api/clubs/favorite_users?code=pppjo')
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['username'] == 'josh'

        print("\n Testing /api/clubs/favorite_users with non_existent club")
        response = self.app.get('/api/clubs/favorite_users?code=non_existent')
        self.assertEqual(response.status_code, 404)

        print("\n Testing /api/clubs/favorite_users without code and name")
        response = self.app.get('/api/clubs/favorite_users')
        self.assertEqual(response.status_code, 406)

    def test_clubs_create(self):
        print("\n Testing /api/clubs/create valid")
        response = self.app.post('/api/clubs/create',data=json.dumps(dict(
            session_key= session_key,
            code= 'pppal',
            name='Penn Pal',
            description='Pen Pal but at Penn',
            tags=['LiTeraRY', 'UnderGRADuate']
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/clubs/create club exists")
        response = self.app.post('/api/clubs/create',data=json.dumps(dict(
            session_key= session_key,
            code= 'pppal',
            name='Penn Pal',
        )))
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/clubs/create missing code and name")
        response = self.app.post('/api/clubs/create',data=json.dumps(dict(
            session_key= session_key,
        )))
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/clubs/create permission denied")
        response = self.app.post('/api/clubs/create',data=json.dumps(dict(
            code= 'pppal',
            name='Penn Pal',
        )))
        self.assertEqual(response.status_code, 404)

    def test_clubs_modify(self):
        print("\n Testing /api/clubs/modify valid")
        response = self.app.post('/api/clubs/modify',data=json.dumps(dict(
            session_key= session_key,
            code= 'pppjo',
            name= 'Penn Pre-Professional Juggling Organization',
            new_data={
                'name': 'Penn Juggle Org',
                'description': 'The best Juggle Org on campus',
                'tags': ['Undergraduate']
            }
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/clubs/modify invalid code")
        response = self.app.post('/api/clubs/modify',data=json.dumps(dict(
            session_key= session_key,
            code= 'pppal',
            name='Penn Pal',
        )))
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/clubs/modify new name causes conflict")
        response = self.app.post('/api/clubs/modify',data=json.dumps(dict(
            session_key= session_key,
            code= 'lorem-ipsum',
            name= 'Penn Lorem Ipsum Club',
            new_data={
                'name': 'Penn Memes Club',
                'description': 'The best Juggle Org on campus',
                'tags': ['Undergraduate']
            }
        )))
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/clubs/modify permission denied")
        response = self.app.post('/api/clubs/modify',data=json.dumps(dict(
            session_key=session_key+"l",
            code= 'pppal',
            name='Penn Pal',
        )))
        self.assertEqual(response.status_code, 404)

    """
        Since all helper functions have been tested thoroughly through
        we will now test only api-specific cases
    """
    def test_clubs_delete(self):
        print("\n Testing /api/clubs/delete valid")
        response = self.app.post('/api/clubs/delete',data=json.dumps(dict(
            session_key= session_key,
            code= 'pppjo',
            name= 'Penn Pre-Professional Juggling Organization',
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/clubs/delete invalid code name pair")
        response = self.app.post('/api/clubs/delete',data=json.dumps(dict(
            session_key= session_key,
            code= 'ppcool',
            name= 'Penn Pal',
        )))
        self.assertEqual(response.status_code, 406)

    def test_user_get(self):
        print("\n Testing /api/clubs/delete valid")
        response = self.app.get('/api/user?username=josh')
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/user/delete username doesnt exists")
        response = self.app.get('/api/user?username=bob')
        self.assertEqual(response.status_code, 404)

    def test_user_favoriting(self):
        print("\n Testing /api/user/favoriting valid")
        response = self.app.post('/api/user/favoriting',data=json.dumps(dict(
            session_key= session_key,
            code= 'pppjo'
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/user/favoriting invalid club code")
        response = self.app.post('/api/user/favoriting',data=json.dumps(dict(
            session_key= session_key,
            code= 'ppcool',
        )))
        self.assertEqual(response.status_code, 406)

    def test_user_favorite_clubs(self):
        print("\n Testing /api/user/favorite_clubs valid")
        response = self.app.get('/api/user/favorite_clubs?username=josh')
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/user/favorite_clubs missing username and email")
        response = self.app.get('/api/user/favorite_clubs')
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/user/favorite_clubs user doesn't exist")
        response = self.app.get('/api/user/favorite_clubs?username=bob')
        self.assertEqual(response.status_code, 404)

    def test_user_login(self):
        print("\n Testing /api/user/login valid")
        response = self.app.post('/api/user/login',data=json.dumps(dict(
            email='josh@upenn.edu',
            password= 'joshiscool'
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/user/login invalid email")
        response = self.app.post('/api/user/login',data=json.dumps(dict(
            email='bobby@upenn.edu',
            password= 'bobbyiscool'
        )))
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/user/login wrong password")
        response = self.app.post('/api/user/login',data=json.dumps(dict(
            email='josh@upenn.edu',
            password= 'joshsucks'
        )))
        self.assertEqual(response.status_code, 404)

    def test_user_signup(self):
        print("\n Testing /api/user/signup valid")
        response = self.app.post('/api/user/signup',data=json.dumps(dict(
            email='bqle@upenn.edu',
            password= 'bqleiscool',
            username= 'bqle'
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/user/signup email already exists")
        response = self.app.post('/api/user/signup',data=json.dumps(dict(
            email='josh@upenn.edu',
            password= 'joshv2',
            username= 'joshv2'
        )))
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/user/signup missing fields")
        response = self.app.post('/api/user/signup',data=json.dumps(dict(
            email='sammy@upenn.edu',
            password= 'sammy'
        )))
        self.assertEqual(response.status_code, 406)

    def test_user_logout(self):
        print("\n Testing /api/user/logout valid")
        response = self.app.post('/api/user/logout',data=json.dumps(dict(
            session_key=session_key
        )))
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/user/logout wrong session_key")
        response = self.app.post('/api/user/logout',data=json.dumps(dict(
            session_key=session_key+"as"
        )))
        self.assertEqual(response.status_code, 404)

        print("\n Testing /api/user/logout no session_key")
        response = self.app.post('/api/user/logout',data=json.dumps(dict(
        )))
        self.assertEqual(response.status_code, 404)

    def test_tag(self):
        print("\n Testing /api/tag exist")
        response = self.app.get('/api/tag')
        json_response = json.loads(response.data)
        print(json_response)
        assert len(json_response) == 7
        self.assertEqual(response.status_code, 200)

    def test_tag_search(self):
        print("\n Testing /api/tag exist")
        response = self.app.get('/api/tag/search?tag=Undergraduate')
        json_response = json.loads(response.data)
        print(json_response)
        assert len(json_response['clubs']) == 4
        self.assertEqual(response.status_code, 200)

        print("\n Testing /api/tag doesn't exist")
        response = self.app.get('/api/tag/search?tag=undergrad')
        self.assertEqual(response.status_code, 406)

        print("\n Testing /api/tag no tag param")
        response = self.app.get('/api/tag/search')
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()