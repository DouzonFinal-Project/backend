import requests
from config.settings import settings

class FrontAPIClient:
    def __init__(self):
        self.base_url = settings.FRONT_API_BASE_URL
        self.token = settings.FRONT_INTERNAL_TOKEN

    def get_example_data(self, payload: dict) -> dict:
        url = f"{self.base_url}/example-endpoint"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

front_client = FrontAPIClient()
