"""
LinkedIn access token

Use this script to get a LinkedIn access token. The script will start a
server and ask for your LinkedIn login credentials. Your new access token
will be printed to the terminal
"""

import os
import webbrowser

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.responses import HTMLResponse

load_dotenv(override=True)


asgi_app = FastAPI()
client_id = os.getenv("LINKEDIN_CLIENT_ID")
client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")

webbrowser.open(
    "https://www.linkedin.com/oauth/v2/authorization?response_type=code&"
    f"client_id={client_id}&redirect_uri"
    "=http://localhost:7878/linkedin/&scope=w_member_social%20openid%20email%20profile"
)


@asgi_app.get("/linkedin/")
def linkedin_login(code):
    try:
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:7878/linkedin/",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        response = requests.post(url, data=params)

        if response.status_code == 200:
            access_token = response.json()["access_token"]
            print("ACCESS TOKEN:")
            print(access_token)
            # redirect the user to your app or just
            return HTMLResponse("Return to to application")
        else:
            return HTMLResponse(f"{response.status_code}: {response.text}")
    except Exception as e:
        print(e)
        return HTMLResponse(e)


if __name__ == "__main__":
    uvicorn.run(asgi_app, host="127.0.0.1", port=7878)
