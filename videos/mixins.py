import os

import requests

class APIReturnedError(Exception):
    """
    The api response contains an error, occurs when response.ok is False
    """
    def __init__(self, error_message=None):
        if error_message:
            self.error_message = error_message

    def __str__(self):
        if self.error_message:
            return repr(self.error_message)
        else:
            return 'Not specified in api response'

class VideoAPIMixin:
    # Constants
    API_URL = 'https://www.googleapis.com/youtube/v3/'
    API_key_file = os.path.join(os.path.dirname(__file__), 'api_key.txt')
    with open(API_key_file, 'r') as f:
        API_KEY = f.read()

    @classmethod
    def get_info_from_api(cls, uri, params):
        url = cls.API_URL + uri
        parameters = {**{'key': cls.API_KEY}, **params}
        response = requests.get(url, params=parameters)
        if response.ok:
            return response.json()
        else:
            raise APIReturnedError(response.json().get('error', None))

    # Protected Methods
    _get_info_from_api = get_info_from_api
