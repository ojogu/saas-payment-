
from .exception import Environment_Variable_Exception

import os
from dotenv import load_dotenv, find_dotenv, set_key
from .exception import Environment_Variable_Exception


def get_env_value(var_name: str) -> str | None:
    """Function to get the value of an environment variable."""
    load_dotenv(find_dotenv())
    value = os.getenv(var_name)
    if value is None:
        raise Environment_Variable_Exception(
            f"Environment variable '{var_name}' not found. Please check your .env file."
        )
    return value

from datetime import datetime
import uuid
def generate_wallet_ref_number(transaction_type: str) -> str:
    """Function to generate a wallet reference number."""
    current_date_time = datetime.now()
    return f"{transaction_type.upper()}-{current_date_time.strftime('%Y-%m-%d_%H-%M-%S.%f')}-{uuid.uuid4()}"
def generate_payment_ref_number(transaction_type: str) -> str:
    """Function to generate a wallet reference number."""
    current_date_time = datetime.now()
    return f"{transaction_type.upper()}-{current_date_time.strftime('%Y-%m-%d_%H-%M-%S.%f')}-{uuid.uuid4()}"
