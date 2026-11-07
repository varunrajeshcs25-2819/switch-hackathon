
from fastapi import FastAPI

# Create our FastAPI application
app = FastAPI()

# First endpoint
@app.get("/")
def home():
    return {
        "message": "DevTeam AI Backend is running!"
    }
