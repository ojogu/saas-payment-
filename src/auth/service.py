from passlib.context import CryptContext

ctx = CryptContext(
    schemes=["bcrypt"]
)

def password_hash(password:str)->str:
    hash = ctx.hash(password)
    return hash 


def verify_password(password, password_hash):
    is_valid = ctx.verify(password, password_hash)
    return is_valid 

