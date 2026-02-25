import requests
import json

def register_test_user():
    url = "http://127.0.0.1:5000/api/register"
    data = {
        "username": "test_asha_1",
        "password": "password123",
        "role": "asha_worker",
        "village_id": 1,
        "name": "Dr. Sunita Sharma",
        "mobile": "9876543210"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        print(f"Registering test user: {data['username']}...")
        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    register_test_user()
