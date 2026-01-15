import os
from typing import Dict, List
from src.model import Organization
import json
from src.utils.db import engine
from sqlalchemy.orm import Session, sessionmaker


#migration process
#1. Convert sqlite tables with it's value to json for better parsing
#2. Level 1 (Independent Tables): Tables with no Foreign Keys (e.g., Users, Categories).
    # Level 2 (Dependent Tables): Tables that reference Level 1 (e.g., Posts that link to Users).
    # Level 3 (Junction Tables): Tables for Many-to-Many relationships (e.g., Post_Tags).


#create a new session, independent of the application session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db:Session = SessionLocal()

# 1. Get the directory where THIS script is saved
script_dir = os.path.dirname(os.path.abspath(__file__))


def load_from_json(json_file:str, cls):
    try:
        # 2. Join that directory with your filename
        file_path = os.path.join(script_dir, json_file)
        with open(file_path) as f:
            data:List[Dict] = json.load(f)
        for d in data:
            obj = cls(**d)
            db.add(obj)
            db.commit()
            print(f"Successfully loaded and saved {cls.__name__} from {json_file}: {obj}")
    except FileNotFoundError:
        print(f"Error: File {json_file} not found.")
        db.rollback()
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        db.rollback()
    except Exception as e:
        print(f"Error: Failed to load {cls.__name__} from {json_file}: {e}")
        db.rollback()

if __name__ == "__main__":
    organization = load_from_json('organizations.json', Organization)
