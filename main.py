from fastapi import FastAPI, HTTPException, Body, Depends, status,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
import openai
from supabase import create_client
from datetime import datetime
import bcrypt
import jwt
from jose import JWTError, jwt

from dotenv import load_dotenv
import os
import traceback
import asyncio
app = FastAPI()

load_dotenv()

# JWT_SECRET = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
# supabase_url = "https://claaenmfimnmsaxsvobz.supabase.co"
# supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNsYWFlbm1maW1ubXNheHN2b2J6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDM0NTYwNDEsImV4cCI6MjAxOTAzMjA0MX0.JJ5X6KayhSP1ZQKuYengZKjLaVqCN14nrSpzfiSqVcQ"
# openai_api_key = "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"

JWT_SECRET = os.getenv("JWT_SECRET")
supabase_url = os.getenv("SUPABASEURL")
supabase_key = os.getenv("SUPABASEKEY")
openai_api_key =os.getenv("OPENAI_API_KEY")

openai.api_key = openai_api_key
supabase = create_client(supabase_url, supabase_key)

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_username(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise credentials_exception


# @app.post("/authtoken")
# async def generate_auth_token(username: str = Body(...), email: str = Body(...)):
#     try:
#         token = jwt.encode({"sub": username, "email": email}, JWT_SECRET, algorithm="HS256")
#         return JSONResponse(content={"token": token, "message": "Token generated successfully"})
#     except Exception as e:
#         print("Error:", e)
#         raise HTTPException(status_code=500, detail="Server Error")


@app.post("/login")
async def login(login_info: dict = Body(...)):
    try:
        email = login_info["email"]
        password = login_info["password"]

        user = supabase.from_("user").select("*").eq("email", email).execute()
        if not user.data:
            return JSONResponse(content={"error": "Invalid email"})

        hashed_password = user.data[0]["password"]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            token = jwt.encode({"sub": user.data[0]["username"], "email": email}, JWT_SECRET, algorithm="HS256")
            return JSONResponse(content={"token": token, "message": "Login successful"})
        else:
            return JSONResponse(content={"error": "Invalid email or password"})

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Server Error")


@app.post("/register")
# async def register(user_info: dict = Body(...), token: str = Depends(oauth2_scheme)):
async def register(user_info: dict = Body(...)):
    try:
        username = user_info["username"]
        email = user_info["email"]
        password = user_info["password"]

        existing_username = supabase.from_("user").select("*").eq("username", username).execute()
        if existing_username.data:
            return JSONResponse(content={"error": "username exists"})

        existing_user = supabase.from_("user").select("*").eq("email", email).execute()
        if existing_user.data:
            return JSONResponse(content={"error": "user with this email already exists"})

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
        token1 = jwt.encode({"username": username, "email": email}, JWT_SECRET, algorithm="HS256")

        new_user = supabase.table("user").upsert(
            {"username": username, "email": email, "password": hashed_password}).execute()

        if new_user.data:
            print("user upserted successfully")
            return JSONResponse(
                content={"token": token1, "message": "User registered successfully", "user": new_user.data})
        else:
            print("Supabase upsert error:", new_user["error"])
            raise HTTPException(status_code=500, detail="Error registering the user")

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Server Error")


@app.post("/stream_chat", response_model=str)
async def stream_chat(prompt: dict = Body(...), username: str = Depends(get_current_username)):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI chatbot. Respond to all input in 25 words or less"},
                {"role": "user", "content": prompt["prompt"]},
            ],
            
        )
        completion = response['choices'][0]['message']['content'].strip()

        conversation_entry = [{"message": prompt["prompt"] + ":" + completion,
                               "timestamp": datetime.now().isoformat()}]
        result = supabase.table("chat_logs").upsert(conversation_entry).execute()

        if result:
            print("data upserted successfully")

        # Generate JWT token for the user
        token = jwt.encode({"sub": username, "email": prompt.get("email")}, JWT_SECRET, algorithm="HS256")

        # Stream the response along with the token
        return f"Token: {token}\nResponse: {completion}"
    except Exception as e:
        print("Error:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Server Error")
    

# @app.post("/stream_chat", response_model=str)
# async def stream_chat(prompt: dict = Body(...), username: str = Depends(get_current_username)):
#     try:
#         # client = OpenAI()

#         stream = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are an AI chatbot. Respond to all input in 25 words or less"},
#                 {"role": "user", "content": prompt["prompt"]},
#             ],
#             stream=True,
#         )

#         completion = ""

#         async for chunk in stream:
#             for choice in chunk.choices:
#                 if choice.message:
#                     completion += choice.message.content

#         conversation_entry = [{"message": prompt["prompt"] + ":" + completion.strip(),
#                                "timestamp": datetime.now().isoformat()}]
#         # Assuming you have defined supabase client somewhere
#         result = supabase.table("chat_logs").upsert(conversation_entry).execute()

#         if result:
#             print("data upserted successfully")

#         # Generate JWT token for the user
#         token = jwt.encode({"sub": username, "email": prompt.get("email")}, JWT_SECRET, algorithm="HS256")

#         # Stream the response along with the token
#         return f"Token: {token}\nResponse: {completion}"
#     except Exception as e:
#         print("Error:", e)
#         print(traceback.format_exc())
#         raise HTTPException(status_code=500, detail="Server Error")


    


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)


