import streamlit as st
import pandas as pd
from authlib.integrations.requests_client import OAuth2Session
from streamlit_gsheets import GSheetsConnection

# --- Streamlit Config ---
st.set_page_config(layout="wide")
st.title("Technical Reports - 2025")
st.markdown("🔑 Please login with Google to access your reports.")

# --- Hide Streamlit Branding ---
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
.viewerBadge_container__1QSob {display: none;}
.st-emotion-cache-12fmjuu {display: none;}
.stActionButton {display: none;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- Google OAuth Config ---
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REDIRECT_URI = "https://technical-activity-report.streamlit.app/"   # ✅ safer with trailing slash
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# --- Gmail to Sheet Mapping ---
TEAM_SHEETS = {
    "daniel@barcotech.net": "Daniel",
    "ronald@barcotech.net": "Ron",
    "ariel@barcotech.net": "Ariel",
    "marlouie@barcotech.net": "Louie",
    "william@barcotech.net": "Bovi",
    "nathaniel@barcotech.net": "Nathan",
    "cjuztin@barcotech.net": "Cj",
    "eduardo@barcotech.net": "Eduardo",
    "camelo@barcotech.net": "Camelo",
    "rye_tabil@barcotech.net": "Rye",
}

WORK_TITLES_SOFTWARE = [
    "System Development","System On-site Meeting","System On-line Meeting",
    "System Demo","Continuation of System Development","Technical Related Task",
    "Not Related Task","On-Line Support",
]

WORK_TITLES_TECHNICAL = [
    "On-Site Support","In-House Repair","On-Site Repair","Diagnostic",
    "Training Installation","Delivery Installation","Service Visit","PMS",
    "Demo","Internal Inquiry",
]

WORK_STATUS = ["Done", "OnGoing"]

# --- Session State Init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = None

# --- Logout Button ---
if st.session_state.logged_in:
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.success("You have been logged out.")
        st.stop()

# --- Step 1: Require login if not logged in ---
if not st.session_state.logged_in:
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = oauth.create_authorization_url(AUTHORIZATION_URL)
    st.markdown(f"[👉 Login with Google]({auth_url})")
    st.stop()

# --- Step 2: The rest of your app (only after login) ---

# --- Connect to Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Map Gmail to Sheet ---
email = st.session_state.email or "replace_with_logged_in_email@domain.com"  # placeholder until real login flow
selected_sheet = TEAM_SHEETS.get(email, None)
if not selected_sheet:
    st.error("🚫 You are not authorized to access this system.")
    st.stop()

# --- Work Titles ---
WORK_TITLES = WORK_TITLES_SOFTWARE if selected_sheet in ["Daniel", "Ron"] else WORK_TITLES_TECHNICAL

# --- Try to read existing data ---
try:
    existing = conn.read(
        worksheet=selected_sheet,
        usecols=list(range(7)),
        header=0,
        ttl=5
    )
    existing["SQ"] = pd.to_numeric(existing.get("SQ", pd.Series(dtype=int)), errors='coerce').fillna(0).astype(int)
except Exception:
    existing = pd.DataFrame(columns=["SQ","Date","Work Title","Sales Name","Work Status","Comments","Cancelled Event"])

# --- Layout: 2 columns ---
col1, col2 = st.columns([1, 3])

# --- Left column: Input Form ---
with col1:
    st.subheader("📝 Input Report")
    with st.form(key="Technical_Report", clear_on_submit=True):
        date = st.date_input("Date*", value=pd.to_datetime("today"))
        work_title = st.selectbox("Work Title*", options=WORK_TITLES)
        sales_name = st.text_input("Sales Name")
        work_status = st.selectbox("Work Status*", options=WORK_STATUS)
        comments = st.text_area("Comments", height=100)
        cancelled_event = st.text_area("Cancelled Event", height=100)

        submit = st.form_submit_button("Submit Report")

        if submit:
            if not work_title:
                st.warning("⚠️ Please select a Work Title.")
                st.stop()

            last_sq = int(existing["SQ"].max()) if not existing.empty else 0

            new_row = pd.DataFrame([{
                "SQ": last_sq + 1,
                "Date": date,
                "Work Title": work_title,
                "Sales Name": sales_name,
                "Work Status": work_status,
                "Comments": comments,
                "Cancelled Event": cancelled_event,
            }])

            updated = pd.concat([existing, new_row], ignore_index=True)

            try:
                conn.update(worksheet=selected_sheet, data=updated)
                st.success(f"✅ Report saved to *{selected_sheet}*! ✅")
                existing = updated
            except Exception as e:
                st.error(f"Failed to update sheet: {e}")

# --- Right column: Excel-like view ---
with col2:
    st.subheader(f"📊 Reports for {selected_sheet}")
    if existing is not None and not existing.empty:
        st.dataframe(existing.reset_index(drop=True), width='stretch', height=700, hide_index=True)
    else:
        st.info("No reports yet. Start adding using the form on the left.")
