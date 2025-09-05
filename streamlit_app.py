import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- Streamlit UI ---
st.set_page_config(layout="wide")  # full-width layout
st.title("Technical Reports - 2025")
st.markdown("Submit your report below. Each team member has their own sheet.")

# --- Connect to Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Team Members (sheet names must match tabs in Google Sheets) ---
TEAM_MEMBERS = [
    "Rye",
    "Ariel",
    "Ron",
    "Louie",
    "Bovi",
    "Nathan",
    "Cj",
    "Eduardo",
    "Camelo",
    "Daniel",
]

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

# --- Select team member (choose sheet) ---
selected_sheet = st.selectbox("Select your name (worksheet):", TEAM_MEMBERS, index=0)

# --- Determine work titles based on role ---
if selected_sheet in ["Daniel", "Ron"]:
    WORK_TITLES = WORK_TITLES_SOFTWARE
else:
    WORK_TITLES = WORK_TITLES_TECHNICAL

# --- Try to read sheet (check if exists) ---
try:
    existing = conn.read(
        worksheet=selected_sheet,
        usecols=list(range(7)),
        header=0,
        ttl=5
    )
except Exception:
    existing = pd.DataFrame(
        columns=[
            "SQ",
            "Date",
            "Work Title",
            "Sales Name",
            "Work Status",
            "Comments",
            "Cancelled Event",
        ]
    )

# --- Layout: 2 columns (small form, big table) ---
col1, col2 = st.columns([1, 3])

# --- Left column: Input Form ---
with col1:
    st.subheader("📝 Input Report")

    with st.form(key="Technical_Report", clear_on_submit=True):
        date = st.date_input("Date*", value=pd.to_datetime("today"))
        work_title = st.selectbox("Work Title*", options=WORK_TITLES, index=None)
        sales_name = st.text_input("Sales Name")
        work_status = st.selectbox("Work Status*", options=WORK_STATUS)

        # Palakihan ang comments at cancelled event
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

            # --- Refresh local data for right column ---
            existing = updated

# --- Right column: Excel-like view ---
with col2:
    st.subheader(f"📊 Reports for {selected_sheet}")
    if existing is not None and not existing.empty:
        # Reset index para mawala yung 0,1,2... sa gilid
        display_df = existing.reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True, height=700, hide_index=True)
    else:
        st.info("No reports yet. Start adding using the form on the left.")
