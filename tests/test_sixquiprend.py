from sixquiprend.sixquiprend import app, db, User, user_manager
from flask import Flask, url_for
import unittest

class SixquiprendTestCase(unittest.TestCase):

    USERNAME = 'User'
    PASSWORD = 'Password1'

    def setUp(self):
        app.config['SERVER_NAME'] = 'localhost'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DATABASE_NAME'] = 'sixquiprend_test'
        db_path = app.config['DATABASE_USER'] + ':' + app.config['DATABASE_PASSWORD']
        db_path += '@' + app.config['DATABASE_HOST'] + '/' + app.config['DATABASE_NAME']
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + db_path
        app.config['TESTING'] = True
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            if not User.query.filter(User.username == 'User').first():
                user = User(username=self.USERNAME,
                        password=user_manager.password_crypt_context.hash(self.PASSWORD))
                db.session.add(user)
                db.session.commit()

    def tearDown(self):
        self.app = app.test_client()
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        with app.app_context():
            self.app.post(url_for('user.login'), data=dict(
                username=self.USERNAME,
                password=self.PASSWORD,
            ), follow_redirects=True)

    def logout(self):
        with app.app_context():
            self.app.get(url_for('user.logout'), follow_redirects=True)

    def test_empty_db(self):
        rv = self.app.get('/')
        assert b'No entries here so far' in rv.data

    def test_messages(self):
        self.login()
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert b'No entries here so far' not in rv.data
        assert b'&lt;Hello&gt;' in rv.data
        assert b'<strong>HTML</strong> allowed here' in rv.data

if __name__ == '__main__':
    unittest.main()