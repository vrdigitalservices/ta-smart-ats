import streamlit as st
import re
import pandas as pd
from collections import Counter
import os
import pdfplumber

# ---------------- CONFIG ----------------
st.set_page_config(page_title="TA Smart ATS", page_icon="💼", layout="wide")

# ---------------- LOGIN ----------------
def login():
    st.title("🔐 Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "admin123":
            st.session_state["login"] = True
        else:
            st.error("Invalid credentials")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ---------------- FUNCTIONS ----------------
def generate_search_strings(jd):
    words = re.findall(r"\b\w+\b", jd.lower())
    words = [w for w in words if len(w) > 4]
    common = [w for w, _ in Counter(words).most_common(8)]

    if len(common) < 2:
        return ["Enter better JD"]

    def get(i):
        return common[i] if i < len(common) else common[-1]

    return [
        f"({get(0)} OR {get(1)}) AND ({get(2)} OR {get(3)})",
        f"{get(0)} AND {get(2)} AND India",
        f"{get(1)} AND {get(3)} experience"
    ]

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_details(text):
    email = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    phone = re.findall(r"\b\d{10}\b", text)

    skills = ["marketing","seo","sales","python","java","sap","hr"]
    found = [s for s in skills if s in text.lower()]

    return {
        "Email": email[0] if email else "",
        "Phone": phone[0] if phone else "",
        "Skills": ", ".join(found)
    }

def match_score(jd, resume):
    jd_words = set(re.findall(r"\w+", jd.lower()))
    resume_words = set(re.findall(r"\w+", resume.lower()))

    if not jd_words:
        return 0

    return int(len(jd_words & resume_words) / len(jd_words) * 100)

# ---------------- DATABASE ----------------
FILE = "candidates.csv"

if not os.path.exists(FILE):
    pd.DataFrame(columns=["Name","Email","Phone","Skills","Score"]).to_csv(FILE, index=False)

# ---------------- UI ----------------
st.title("💼 TA Smart ATS")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Job Description")
    jd = st.text_area("Paste JD")

    if st.button("Generate Strings"):
        for s in generate_search_strings(jd):
            st.code(s)

with col2:
    st.subheader("📑 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])

    resume_text = ""
    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)
        st.success("Resume parsed successfully")

        if st.checkbox("Show Resume Text"):
            st.text_area("Content", resume_text, height=200)

        details = extract_details(resume_text)

        st.text_input("Email", value=details["Email"])
        st.text_input("Phone", value=details["Phone"])
        st.text_input("Skills", value=details["Skills"])

# Match
if st.button("Check Match"):
    score = match_score(jd, resume_text)
    st.metric("Match %", f"{score}%")

# Save
st.subheader("💾 Save Candidate")

name = st.text_input("Name")
email = st.text_input("Email (manual)")
phone = st.text_input("Phone (manual)")
skills = st.text_input("Skills (manual)")

if st.button("Save Candidate"):
    score = match_score(jd, resume_text)

    df = pd.read_csv(FILE)
    new = pd.DataFrame([[name,email,phone,skills,score]], columns=df.columns)
    df = pd.concat([df,new], ignore_index=True)
    df.to_csv(FILE, index=False)

    st.success("Candidate saved")

# View DB
st.subheader("📊 Candidate Database")
df = pd.read_csv(FILE)
st.dataframe(df)

# ---------------- DISCLAIMER ----------------
st.markdown("---")
st.markdown(
    "<center><small>This application was developed by Rajkumar with the assistance of ChatGPT for professional recruitment purposes.</small></center>",
    unsafe_allow_html=True
)
