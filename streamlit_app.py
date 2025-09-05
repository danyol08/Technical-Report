import streamlit as st
import pandas as pd
import requests
from authlib.integrations.requests_client import OAuth2Session
from streamlit_gsheets import GSheetsConnection

st.markdown(
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    </style>
    ,
    unsafe_allow_html=True
)



# --- Streamlit Config ---
st.set_page_config(layout="wide")
st.title("Technical Reports - 2025")
st.markdown("🔑 Please login with Google to access your reports.")

# --- Google OAuth Config ---
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REDIRECT_URI = "https://technical-activity-report.streamlit.app"   
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# --- Gmail to Sheet Mapping ---
TEAM_SHEETS = {
    "daniel@barcotech.net": "Daniel",
    "ronald@barcotech.net": "Ron",
    "ariel@gmail.com": "Ariel",
    "marlouie@barcotech.net": "Louie",
    "bovi@gmail.com": "Bovi",
    "nathan@gmail.com": "Nathan",
    "cj@gmail.com": "Cj",
    "eduardo@gmail.com": "Eduardo",
    "camelo@gmail.com": "Camelo",
    "rye@gmail.com": "Rye",
}

# --- Work Titles ---
WORK_TITLES_SOFTWARE = [
    "System Development",
    "System On-site Meeting",
    "System On-line Meeting",
    "System Demo",
    "Continuation of System Development",
    "Technical Related Task",
    "Not Related Task",
    "On-Line Support",
]

WORK_TITLES_TECHNICAL = [
    "On-Site Support",
    "In-House Repair",
    "On-Site Repair",
    "Diagnostic",
    "Training Installation",
    "Delivery Installation",
    "Service Visit",
    "PMS",
    "Demo",
    "Internal Inquiry",
]

WORK_STATUS = ["Done", "OnGoing"]

# --- Step 1: If not logged in, show login button ---
if "token" not in st.session_state:
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = oauth.create_authorization_url(AUTHORIZATION_URL)
    st.markdown(f"[👉 Login with Google]({auth_url})")

# --- Step 2: Handle OAuth Redirect ---
if "code" in st.query_params and "token" not in st.session_state:
    code = st.query_params["code"]
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI,
    )
    token = oauth.fetch_token(TOKEN_URL, code=code)
    st.session_state["token"] = token

# --- Step 3: If logged in, fetch user info ---
if "token" in st.session_state:
    token = st.session_state["token"]
    resp = requests.get(USERINFO_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
    user_info = resp.json()

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

    # --- Work Titles based on role ---
    if selected_sheet in ["Daniel", "Ron"]:
        WORK_TITLES = WORK_TITLES_SOFTWARE
    else:
        WORK_TITLES = WORK_TITLES_TECHNICAL

    # --- Try to read existing data ---
    try:
        existing = conn.read(
            worksheet=selected_sheet,
            usecols=list(range(7)),
            header=0,
            ttl=5
        )
    except Exception:
        existing = pd.DataFrame(columns=["SQ","Date","Work Title","Sales Name","Work Status","Comments","Cancelled Event"])

    # --- Layout: 2 columns ---
    col1, col2 = st.columns([1, 3])

    # --- Left column: Input Form ---
    with col1:
        st.subheader("📝 Input Report")

        with st.form(key="Technical_Report", clear_on_submit=True):
            date = st.date_input("Date*", value=pd.to_datetime("today"))
            work_title = st.selectbox("Work Title*", options=WORK_TITLES, index=None)
            sales_name = st.text_input("Sales Name")
            work_status = st.selectbox("Work Status*", options=WORK_STATUS)
            comments = st.text_area("Comments", height=100)
            cancelled_event = st.text_area("Cancelled Event", height=100)

            submit = st.form_submit_button("Submit Report")

            if submit:
                if not work_title:
                    st.warning("⚠️ Please select a Work Title.")
                    st.stop()

                # --- Get last SQ ---
                if existing is None or existing.empty:
                    last_sq = 0
                else:
                    try:
                        last_sq = int(existing["SQ"].max())
                    except Exception:
                        last_sq = 0

                # --- New row ---
                new_row = pd.DataFrame([{
                    "SQ": last_sq + 1,
                    "Date": date,
                    "Work Title": work_title,
                    "Sales Name": sales_name,
                    "Work Status": work_status,
                    "Comments": comments,
                    "Cancelled Event": cancelled_event,
                }])

                # --- Append row ---
                updated = pd.concat([existing, new_row], ignore_index=True)

                # --- Update sheet ---
                conn.update(worksheet=selected_sheet, data=updated)

                st.success(f"✅ Report saved to *{selected_sheet}*! (SQ {last_sq + 1})")
                existing = updated

    # --- Right column: Excel-like view ---
    with col2:
        st.subheader(f"📊 Reports for {selected_sheet}")
        if existing is not None and not existing.empty:
            display_df = existing.reset_index(drop=True)
            st.dataframe(display_df, use_container_width=True, height=700, hide_index=True)
        else:
            st.info("No reports yet. Start adding using the form on the left.")

