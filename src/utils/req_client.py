import requests

class HttpConfig:
    _instance = None
    _session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_session(self):
        if self._session is None:
            self._session = requests.Session()
            # Note: Connection limits and tracing are handled differently in requests
            # Default timeout can be set per request
        return self._session

    def close(self):
        if self._session:
            self._session.close()
            self._session = None

http_client = HttpConfig()

# Usage examples:
# session = http_client.get_session()
# response = session.get('https://api.example.com/data', timeout=30)
# response = session.post('https://api.example.com/data', json={'key': 'value'}, timeout=30)
# http_client.close()
