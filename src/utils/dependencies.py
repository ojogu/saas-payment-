from flask_jwt_extended import JWTManager
from flask import Flask
from dishka import make_container, Provider, Scope, provide
from dishka.integrations.flask import setup_dishka
from src.service.organization_service import OrganizationService
from src.service.user_service import UserService
from src.utils.db import db as database_session
from sqlalchemy.orm import Session

jwt = JWTManager()

class Dependencies(Provider):
    @provide(scope=Scope.APP)  # Create once, reuse forever
    def database(self)-> Session:
        return database_session
    
    @provide(scope=Scope.REQUEST)  # Create new for each HTTP request
    def organization_service(self, db: Session) -> OrganizationService:
        return OrganizationService(db)
    
    @provide(scope=Scope.REQUEST)  # Create new for each HTTP request
    def user_service(self, db: Session) -> UserService:
        return UserService(db)
    
    
def setup_dependencies(app:Flask):
    container = make_container(Dependencies())
    setup_dishka(container, app, auto_inject=True)
