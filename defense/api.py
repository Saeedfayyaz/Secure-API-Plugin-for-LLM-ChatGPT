import requests

url = "http://127.0.0.1:8000/weather"
data = {
    "location": "Sydney"
}

response = requests.post(url, json=data)

print(response.status_code)
print(response.json())
