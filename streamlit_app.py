import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- Streamlit Config ---
st.set_page_config(layout="wide")
st.title("Technical Reports - 2025")
st.markdown("🔑 Login with your allowed Google account to access your report.")

# --- Allowed Google accounts mapping to sheets ---
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

# --- Step 1: Simple "login" using email input ---
if "email" not in st.session_state:
    email = st.text_input("Enter your Google email to login:")
    if st.button("Login"):
        email = email.strip().lower()
        if email in TEAM_SHEETS:
            st.session_state["email"] = email
            st.experimental_rerun()
        else:
            st.error("🚫 Unauthorized email. You cannot access this system.")
else:
    email = st.session_state["email"]
    selected_sheet = TEAM_SHEETS[email]
    st.success(f"✅ Logged in as {email}")
    st.info(f"📊 You only have access to sheet: **{selected_sheet}**")

    # --- Connect to Google Sheets ---
    conn = st.connection("gsheets", type=GSheetsConnection)

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

    if selected_sheet in ["Daniel", "Ron"]:
        WORK_TITLES = WORK_TITLES_SOFTWARE
    else:
        WORK_TITLES = WORK_TITLES_TECHNICAL

    # --- Try to read sheet ---
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
    col1, col2 = st.columns([1,3])

    # --- Left: Input Form ---
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
                conn.update(worksheet=selected_sheet, data=updated)
                st.success(f"✅ Report saved to *{selected_sheet}*! (SQ {last_sq + 1})")
                existing = updated

    # --- Right: Excel-like view ---
    with col2:
        st.subheader(f"📊 Reports for {selected_sheet}")
        if not existing.empty:
            st.dataframe(existing.reset_index(drop=True), width='stretch', height=700, hide_index=True)
        else:
            st.info("No reports yet. Start adding using the form on the left.")
