from sixquiprend.sixquiprend import app

# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DATABASE_USER='sixquiprend',
    DATABASE_PASSWORD='sixquiprend',
    DATABASE_HOST='localhost',
    DATABASE_NAME='sixquiprend',
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin',
))
app.config.from_envvar('SIXQUIPREND_SETTINGS', silent=True)
db_path = app.config['DATABASE_USER'] + ':' + app.config['DATABASE_PASSWORD']
db_path += '@' + app.config['DATABASE_HOST'] + '/' + app.config['DATABASE_NAME']
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + db_path