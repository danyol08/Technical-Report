import streamlit as st
import pandas as pd
import requests
from authlib.integrations.requests_client import OAuth2Session
from streamlit_gsheets import GSheetsConnection

# --- Streamlit Config ---
st.set_page_config(layout="wide")
st.title("Technical Reports - 2025")
st.markdown("🔑 Please login with Google to access your reports.")

# --- Hide Streamlit Branding ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}
    </style>
""", unsafe_allow_html=True)

# --- OAuth Config ---
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REDIRECT_URI = "https://technical-activity-report.streamlit.app"  # must match Google Cloud
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# --- Gmail to Sheet Mapping ---
TEAM_SHEETS = {
    "daniel@barcotech.net": "Daniel",
    "ronald@barcotech.net": "Ron",
    "ariel@barcotech.net": "Ariel",
    # ... add the rest
}

# --- Step 1: Initialize session state ---
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

# --- Step 2: Handle OAuth Redirect ---
if st.session_state["token"] is None:
    if "code" in st.query_params:
        code = st.query_params["code"][0]  # auth code from URL
        oauth = OAuth2Session(
            CLIENT_ID,
            CLIENT_SECRET,
            scope="openid email profile",
            redirect_uri=REDIRECT_URI,
        )
        # fetch token and store in session_state
        st.session_state["token"] = oauth.fetch_token(TOKEN_URL, code=code)
        st.experimental_rerun()  # reload page with token stored

# --- Step 3: Show login button if no token ---
if st.session_state["token"] is None:
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = oauth.create_authorization_url(AUTHORIZATION_URL)
    st.markdown(f"[👉 Login with Google]({auth_url})")
    st.stop()  # stop until user logs in

# --- Step 4: Fetch user info once ---
if st.session_state["user_info"] is None:
    token = st.session_state["token"]
    resp = requests.get(USERINFO_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
    st.session_state["user_info"] = resp.json()

user_info = st.session_state["user_info"]
email = user_info.get("email", "").lower()
name = user_info.get("name", email)

st.success(f"✅ Logged in as {name} ({email})")

if email not in TEAM_SHEETS:
    st.error("🚫 You are not authorized to access this system.")
    st.stop()

# --- Map Gmail to Sheet ---
selected_sheet = TEAM_SHEETS[email]
st.info(f"📊 You only have access to sheet: **{selected_sheet}**")

# --- Connect to Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Continue with your form / table logic ---
