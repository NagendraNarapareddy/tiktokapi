from flask import Flask, redirect, request, session, jsonify,render_template
import requests
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = "asldfmlalj8q7iqnqoiyioaiahlk"  # Change this!

# TikTok App Credentials (replace with yours)
CLIENT_KEY = "sbawkbclchq1cm2dgi"
CLIENT_SECRET = "iY9uyEelgh7viCEN7pToxD8PDJY7nC6p"
REDIRECT_URI = "https://tiktokapi-mowy.onrender.com/callback"  # Must match TikTok Dev Portal

VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/?fields=id,title,cover_image_url"

@app.route('/')
def home():
    # Create auth URL and redirect to TikTok
    params = {
        'client_key': CLIENT_KEY,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'user.info.basic,video.list',  # Added 'video.list' scope
    }
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Get the auth code from callback URL
    code = request.args.get('code')
    
    # Exchange code for access token
    token_data = {
        'client_key': CLIENT_KEY,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    token_response = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/", 
        data=token_data
    ).json()

    # Store the access token in session
    access_token = token_response.get('access_token')
    if access_token:
        session['access_token'] = access_token
        return redirect('/dashboard')  # Redirect to the dashboard after callback

@app.route('/dashboard')
def dashboard():
    if "access_token" not in session:
        return {"error": "You need to login first."}, 401

    headers = {
        "Authorization": f"Bearer {session['access_token']}",
        "Content-Type": "application/json"
    }

    # Fetch user info
    user_info_response = requests.get("https://open.tiktokapis.com/v2/user/info/", headers=headers,params={"fields": "unique_id,display_name,avatar_url"}).json()

    # Fetch videos
    params = {"max_count": 5, "fields": "id,title,cover_image_url"}
    video_response = requests.post(VIDEO_LIST_URL, headers=headers, params=params).json().get('data', {}).get('videos', [])
    
    embed_codes = []
    for video in video_response:
        # Fetch the embed code using TikTok oEmbed API
        video_url = f"https://www.tiktok.com/@{user_info_response['data']['user']['display_name']}/video/{video['id']}"
        oembed_url = f"https://www.tiktok.com/oembed?url={video_url}"
        embed_response = requests.get(oembed_url).json()
        
        embed_code = embed_response.get('html')
        embed_codes.append(embed_code)
    

    return render_template('home.html', user_info=user_info_response['data'],embed_codes=embed_codes)

if __name__ == '__main__':
    app.run(debug=True)
