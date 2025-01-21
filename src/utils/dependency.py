#this module contains all the dependencies of the application
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_cors import CORS
# Creating instances of each extension class
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
api = Api()
jwt = JWTManager()
ma = Marshmallow()
cors = CORS()