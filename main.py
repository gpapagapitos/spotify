import os
from flask import Flask, redirect, request, jsonify, session
from datetime import datetime
from os.path import join, dirname
from dotenv import load_dotenv
import urllib.parse
import requests

dotenv_path = join(dirname(__file__), '.env')
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(64)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5005/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

@app.route("/")
def index():
    return "<a href='/login'>Login to Spotify</a>"

@app.route("/login")
def login():
    scope = "user-read-private user-read-email"
    params = {
        "client_id": CLIENT_ID,
        "scope": scope,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "show_dialog": True,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error": request.args["error"]})
    if "code" in request.args:
        req_body = {
            "code": request.args["code"],
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()
        session["access_token"] = token_info["access_token"]
        session["refresh_token"] = token_info["refresh_token"]
        session["expires_in"] = datetime.now().timestamp() + 10
        return redirect("/playlists")
    
@app.route("/playlists")
def get_playlists():
    if "access_token" not in session:
        return redirect("/login")
    if session["expires_in"] < datetime.now().timestamp():
        print("TOKEN EXPIRED, REFRESHING...")
        return redirect("/refresh-token")
    headers = {
        "Authorization": f"Bearer {session['access_token']}",
    }
    response = requests.get(API_BASE_URL + "me/playlists", headers=headers)
    playlists = response.json()
    return jsonify(playlists)

@app.route("/refresh-token")
def refresh_token():
    if "refresh_token" not in session:
        return redirect("/login")
    if session["expires_in"] < datetime.now().timestamp():
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        session["access_token"] = new_token_info["access_token"]
        session["expires_in"] = datetime.now().timestamp() + 10
        return redirect("/playlists")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5005)