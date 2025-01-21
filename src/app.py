from flask import Flask
from api.v1.super_admin.routes import super_admin_blueprint
from utils.exception import exception_blueprint
from api.v1.auth.super_admin_auth import super_admin_auth_blueprint
from api.v1.auth.users_auth import user_auth_blueprint
from api.v1.users.admins.routes import admin_blueprint
from api.v1.users.subadmin.routes import subadmin_blueprint
from api.v1.users.students.routes import student_blueprint
from api.v1.reciepts.routes import analytics_blueprint
from utils.config import DevelopmentConfig, ProductionConfig
import utils.dependency as ext
import utils.log as log
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # #initializing the extensions 
    ext.bcrypt.init_app(app)
    ext.jwt.init_app(app)
    ext.db.init_app(app)
    ext.migrate.init_app(app, ext.db)
    # ext.ma.init_app(app)
    
    #cors configuration
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    # CORS(app, resources={r"/auth/*": {"origins": "http://localhost:3002"}}, supports_credentials=True)
    
    
    # ext.cors.init_app(app, resources={r"/*": {"origins": "http://localhost:3002", "methods": ["GET", "POST", "PUT", "DELETE"], "allow_headers": ["Content-Type", "Authorization", "access-control-allow-origin"]}, supports_credentials=True})

#     CORS(app, resources={
#     r"/*": {  # Allow all routes
#         "origins": ["http://localhost:3002"],  # Replace with your frontend URL
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type"]
#     }
# })

    #register blueprint
    app.register_blueprint(exception_blueprint)
    app.register_blueprint(super_admin_auth_blueprint)
    app.register_blueprint(super_admin_blueprint)
    app.register_blueprint(user_auth_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(subadmin_blueprint)
    app.register_blueprint(student_blueprint)
    app.register_blueprint(analytics_blueprint)
    
    #checks the route and blueprint registered to the flask app
    # print("Registered Blueprints:", app.blueprints)
    # print("URL Map:", app.url_map)
    
    #initalize root log
    log.setup_logging()

    return app


if __name__ == "__main__":
    app = create_app()
    root_logger, cors_logger = log.setup_logging()
    
    root_logger.info("Application started")
    cors_logger.info("debugging cors")
    app.run(debug=True, host='0.0.0.0', port=5000)



