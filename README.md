# FastAPI Chat Application

This is a simple chat application built with FastAPI, using OpenAI's GPT-3.5 for generating responses and Supabase for user authentication and chat logs storage.

## Requirements

- Python 3.8 or higher
- Docker (optional, for containerization)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adnankhan47/chat_application_fastapi.git
Navigate to the project directory:
cd chat_application_fastapi
Install dependencies:
pip install -r requirements.txt

Usage
Running Locally
Make sure you have set up your environment variables in a .env file. 

Run the FastAPI application using Uvicorn:
uvicorn main:app --reload
Access the application in your browser at http://localhost:8000.


Docker
Build the Docker image:
docker build -t my-fastapi-app .

Run the Docker container:
docker run -d -p 8000:8000 my-fastapi-app

Access the application in your browser at http://localhost:8000.



API Endpoints
POST /login: Endpoint for user login. Requires email and password in the request body.

POST /register: Endpoint for user registration. Requires username, email, and password in the request body.

POST /stream_chat: Endpoint for streaming chat. Requires a prompt in the request body and a bearer token in Authorization header that was generated after login.
