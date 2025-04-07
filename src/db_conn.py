from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def configure_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:dUUG%c)22Q3O@localhost/emails'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

if __name__ == "__main__":
    pass
