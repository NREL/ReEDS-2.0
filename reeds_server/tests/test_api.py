""" Module for API testing. """

import requests

BASE_URL = 'http://localhost:5001'

def test_health_check():
    
    response = requests.get(BASE_URL + '/api/health')
    assert response.status_code == 200
    assert response.json() == {'message': 'UP and running!'}