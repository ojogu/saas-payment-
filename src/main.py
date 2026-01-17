from flask import Flask
from src.auth.routes import auth_bp
from src.routes.organization_routes import organization_routes
from src.routes.department_routes import department_routes
from src.routes.user_routes import user_routes
from src.routes.clearance_routes import clearance_bp
from src.routes.session_routes import session_route
from src.routes.bursar_routes import bursar_route
from src.routes.faculty_routes import faculty_routes
from src.routes.account_routes import account_bp
from src.routes.clearance_points import clearance_point
from src.routes.payment_routes import payment_routes
from src.routes.log_routes import clearance_log
from src.routes.analytic_routes import analytics_route
from src.routes.notification_routes import notification_routes
from src.routes.clearance_edit_routes import clearance_edits
from src.utils.db import create_tables, drop_tables, init_db, close_db, debug_database
from flask_cors import CORS
from src.utils.config import Settings, app_config
from src.utils.exception import register_error_handlers
from src.utils.dependencies import jwt, setup_dependencies

def create_app():
    app=Flask(__name__)
    
    #db configs
    drop_tables(app)
    create_tables(app)
    init_db(app)
    close_db(app)
    debug_database()
    

    
    jwt.init_app(app)
    
    # Load configuration from Pydantic Settings
    app_config(app)
    
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    #register blueprints
    app.register_blueprint(auth_bp, url_prefix=f"{Settings.API_PREFIX}/auth")
    app.register_blueprint(organization_routes,url_prefix="/api")
    app.register_blueprint(department_routes,url_prefix="/api")
    app.register_blueprint(user_routes,url_prefix="/api")
    app.register_blueprint(clearance_bp,url_prefix="/api")
    app.register_blueprint(bursar_route,url_prefix="/api")
    app.register_blueprint(session_route,url_prefix="/api")
    app.register_blueprint(faculty_routes,url_prefix="/api")
    app.register_blueprint(account_bp,url_prefix="/api")
    app.register_blueprint(clearance_point,url_prefix="/api")
    app.register_blueprint(payment_routes,url_prefix="/api")
    app.register_blueprint(clearance_log,url_prefix="/api")
    app.register_blueprint(analytics_route,url_prefix="/api")
    app.register_blueprint(notification_routes, url_prefix = "/api")
    app.register_blueprint(clearance_edits, url_prefix = "/api")

    #error handling
    register_error_handlers(app)
    
    #setup depedencies
    setup_dependencies(app)
    return app

app = create_app()

#home
@app.route("/api")
def index():
    return {"msg": "successful"}
if __name__=='__main__':
    app.run(debug=True)
    
    
