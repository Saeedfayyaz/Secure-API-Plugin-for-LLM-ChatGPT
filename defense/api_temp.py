import requests
import json

url = "http://127.0.0.1:8000/weather"
data = {
    "location": "Sydney"
}

response = requests.post(url, json=data)
response_json = response.json()

print("Original Weather Data:")
print(response_json)

response_json['current']['temp_c'] =  17.8

print("\nTampered Weather Data:")
print(json.dumps(response_json, indent=2))

url_verify = "http://127.0.0.1:8000/verify_hash"
verification_response = requests.post(url_verify, json=response_json)

print("\nTampered Data Verification Response:")
print(verification_response.status_code)
print(verification_response.json())
