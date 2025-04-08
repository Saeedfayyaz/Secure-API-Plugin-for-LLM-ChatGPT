import httpx
from fastapi import FastAPI, HTTPException
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
import time
import hashlib  # For hashing the API response
from schema import WeatherRequest
import json

app = FastAPI()

BASE_URL = "https://api.weatherapi.com/v1/current.json?"
API_KEY = "dfa71d624d70486cb70131629230908"
LOCATION = "Karachi"

VALID_LOCATIONS = {
    "Karachi", "London", "New York", "Tokyo", "Paris", "Los Angeles", 
    "Mumbai", "Toronto", "Sydney", "Berlin"
}

with open("private_key.pem", "rb") as key_file:
    private_key = serialization.load_pem_private_key(key_file.read(), password=None)

with open("public_key.pem", "rb") as key_file:
    public_key = serialization.load_pem_public_key(key_file.read())

rate_limit_store = {}

# RSA Encryption functions
def encrypt_data(data: str) -> bytes:
    return public_key.encrypt( # type: ignore
        data.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

def decrypt_data(encrypted_data: bytes) -> str:
    return private_key.decrypt( # type: ignore
        encrypted_data,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    ).decode()

def generate_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def rate_limiter(client_id: str, max_requests: int, timeframe: int):
    current_time = time.time()

    if client_id not in rate_limit_store:
        rate_limit_store[client_id] = []
    
    request_times = rate_limit_store[client_id]
    request_times = [t for t in request_times if current_time - t < timeframe]

    if len(request_times) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    request_times.append(current_time)
    rate_limit_store[client_id] = request_times

async def fetch_weather_data(location: str):
    BASE_URL = "https://api.weatherapi.com/v1/current.json?"
    api_key_encrypted = encrypt_data(API_KEY)  
    decrypted_api_key = decrypt_data(api_key_encrypted) 

    url = f"{BASE_URL}key={decrypted_api_key}&q={location}&aqi=no"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error fetching weather data.")
        
        response_text = response.text
        response_hash = generate_hash(response_text) 
        
        return {"data": response.json(), "hash": response_hash, "raw_data": response_text}

def verify_response_hash(raw_data: str, received_hash: str) -> bool:
    generated_hash = generate_hash(raw_data)
    return generated_hash == received_hash

@app.post("/weather")
async def get_weather(data: WeatherRequest, client_id: str = "default-client"):
    if not data.location.isalpha():
        raise HTTPException(status_code=400, detail="Invalid location name. Only alphabets allowed.")
    elif data.location not in VALID_LOCATIONS:
        raise HTTPException(status_code=400, detail="Invalid location name. Please provide a valid city name.")

    rate_limiter(client_id, max_requests=5, timeframe=60)
    
    # Fetch weather data and hash
    weather_response = await fetch_weather_data(data.location)
    weather_data = weather_response['data']
    weather_hash = weather_response['hash']
    raw_data = weather_response['raw_data']  
    
    if not verify_response_hash(raw_data, weather_hash):
        raise HTTPException(status_code=400, detail="Tampered data detected.")
    
    return weather_data
