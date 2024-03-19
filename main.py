from fastapi import FastAPI, HTTPException, Body, Depends, status,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from openai import OpenAI
from supabase import create_client
from datetime import datetime
import bcrypt
import jwt
from jose import JWTError, jwt
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
import traceback
import asyncio
from supabase_psyocpg_connector import db_connection

app = FastAPI()

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
supabase_url = os.getenv("SUPABASEURL")
supabase_key = os.getenv("SUPABASEKEY")
openai_api_key =os.getenv("OPENAI_API_KEY")
client = OpenAI()
# openai.api_key = openai_api_key
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


# async def fake_video_streamer():
#     for i in range(100):
#         yield "data: some fake video bytes\n\n"


@app.get("/get_all_user")
def read_root():
    # data, count = supabase.table("tts_voice_style").select("*").execute()

    with db_connection as cursor:
        cursor.execute("SELECT * FROM public.user")
        data = cursor.fetchall()
        data = [dict(row) for row in data]
        return data


@app.post("/login")
async def login(login_info: dict = Body(...)):
    try:
        email = login_info["email"]
        password = login_info["password"]

        with db_connection as cursor:
            cursor.execute("SELECT * FROM public.user WHERE email=%s", (email,))
            user = cursor.fetchone()
            if not user:
                return JSONResponse(content={"error": "Invalid email"})

            hashed_password = user["password"]
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                token = jwt.encode({"sub": user["username"], "email": email}, JWT_SECRET, algorithm="HS256")
                return JSONResponse(content={"token": token, "message": "Login successful"})
            else:
                return JSONResponse(content={"error": "Invalid email or password"})

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Server Error")


@app.post("/register")
async def register(user_info: dict = Body(...)):
    try:
        username = user_info["username"]
        email = user_info["email"]
        password = user_info["password"]

        with db_connection as cursor:
            cursor.execute("SELECT * FROM public.user WHERE username=%s", (username,))
            existing_username = cursor.fetchone()
            if existing_username:
                return JSONResponse(content={"error": "username exists"})

            cursor.execute("SELECT * FROM public.user WHERE email=%s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                return JSONResponse(content={"error": "user with this email already exists"})

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
            token = jwt.encode({"username": username, "email": email}, JWT_SECRET, algorithm="HS256")

            cursor.execute("INSERT INTO public.user (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))

            return JSONResponse(content={"token": token, "message": "User registered successfully"})

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Server Error")




#orignal
@app.post("/stream_chat", response_model=str)
async def stream_chat(prompt: dict = Body(...), username: str = Depends(get_current_username)):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI chatbot. Respond to all input in 25 words or less"},
                {"role": "user", "content": prompt["prompt"]},
            ],
            
        )
        completion = response.choices[0].message.content

        # conversation_entry = [{"message": prompt["prompt"] + ":" + completion,
        #                        "timestamp": datetime.now().isoformat()}]
        # result = supabase.table("chat_logs").upsert(conversation_entry).execute()

        with db_connection as cursor:
            cursor.execute("INSERT INTO chat_logs (message, timestamp) VALUES (%s, %s)", (prompt["prompt"] + ":" + completion, datetime.now().isoformat()))
        # print("data upserted successfully")

        
        token = jwt.encode({"sub": username, "email": prompt.get("email")}, JWT_SECRET, algorithm="HS256")

        # Stream the response along with the token
        # return f"Response: {completion}"
        return JSONResponse(content={"Response": completion, "message": "Data upserted successfully"})
        # return StreamingResponse(completion, media_type="text/event-stream")

    except Exception as e:
        print("Error:", e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Server Error")
    


@app.post("/streaming_chat1")
async def stream_chat(prompt: dict = Body(...), username: str = "test_user"):
    async def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI chatbot. Respond to all input in 100 words or less"},
                    {"role": "user", "content": prompt["prompt"]},
                ],
                stream=True,
            )
            completion = ""

            for chunk in stream:
                # for choice in chunk.choices:
                if chunk.choices[0].delta.content is not None:
                    # if choice.message.content:
                    completion+=chunk.choices[0].delta.content
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
                    
                    
            # yield f"data: {completion}\n\n"
            # print(completion)
            with db_connection as cursor:
                cursor.execute("INSERT INTO chat_logs (message, timestamp) VALUES (%s, %s)", (prompt["prompt"] + ":" + completion, datetime.now().isoformat()))

        except Exception as e:
            print("OpenAI Response (Streaming) Error: " + str(e))
            raise HTTPException(status_code=503, detail="OpenAI Response Error")

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.exception_handler(Exception)
async def server_error_handler(request, exc):
    print("Error:", exc)
    print(traceback.format_exc())
    return HTTPException(status_code=500, detail="Server Error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)


