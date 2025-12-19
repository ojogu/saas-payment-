from sqlalchemy.orm import Session

class AccountService():
    def __init__(self, db: Session):
        self.db = db 