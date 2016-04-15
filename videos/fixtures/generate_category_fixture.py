import os

import json

import requests

if __name__ == '__main__':
    API_key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                'api_key.txt')
    fixture_file = os.path.join(os.path.dirname(__file__),
                                'category_fixture.json')
    with open(API_key_file, 'r') as f:
        API_key = f.read()
    parameters = dict(part='snippet', regionCode='US', key=API_key)
    url = 'https://www.googleapis.com/youtube/v3/videoCategories'
    JSON = requests.get(url, params=parameters).json()
    fixture = [dict(model='videos.category',
                    pk=data['id'],
                    fields= {'title': data['snippet']['title']})
               for data
               in JSON['items']]
    with open(fixture_file, 'w') as f:
        json.dump(fixture, f)
