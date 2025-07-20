from typing import Tuple, Dict
import os
import json
import requests
import PyPDF2
from datetime import datetime, timedelta
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(page_title="Dobby Recruitment System", layout="wide")

def set_modern_style():
    st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
                background: #f5f6fa !important;
                color: #222 !important;
            }
            [data-testid="stSidebar"] {
                box-shadow: 2px 0 16px #ececec !important;
            }
            [data-testid="stSidebar"] * { color: #222 !important; }
            h1, h2, h3, h4, h5, h6, label, div, p, span { color: #222 !important; }

            /* Modern silvery 3D look for all buttons and button-like elements */
            .stButton > button, .stDownloadButton > button,
            .stFileUploader .css-1umw1f3, .stFileUploader button,
            [data-testid="baseButton-secondary"], [data-testid="baseButton-secondaryForm"] {
                background: #e0e1e3 !important;
                color: #222 !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                border: 1.5px solid #babbbb !important;
                box-shadow: 0 1.5px 6px #e6e7eb !important;
                transition: 0.08s filter;
            }
            .stButton > button:hover, .stDownloadButton > button:hover,
            .stFileUploader .css-1umw1f3:hover, .stFileUploader button:hover,
            [data-testid="baseButton-secondary"]:hover, [data-testid="baseButton-secondaryForm"]:hover {
                filter: brightness(0.96) !important;
                border: 1.5px solid #888 !important;
            }
            /* Fix for all popovers, dropdowns, selects, and file uploader popups */
            div[data-baseweb="popover"], div[data-baseweb="menu"], div[data-baseweb="option"] {
                background: #e0e1e3 !important;
                color: #222 !important;
                border-radius: 10px !important;
            }
            div[data-baseweb="option"]:hover, div[data-baseweb="option"]:active, div[data-baseweb="option"][aria-selected="true"] {
                background: #d4d6da !important;
                color: #222 !important;
            }
            .stSelectbox div[data-baseweb="select"] > div {
                background-color: #e0e1e3 !important;
                color: #222 !important;
            }
            .stSelectbox div[data-baseweb="select"] input {
                background: #e0e1e3 !important;
                color: #222 !important;
            }
            .stSelectbox label, .stSelectbox span, .stSelectbox p, .stSelectbox div {
                color: #222 !important;
            }
            /* Eye icon and eye container for password fields */
            .stTextInput [data-testid="stWidgetIcon"], .stPassword [data-testid="stWidgetIcon"] {
                background: #e0e1e3 !important;
                color: #222 !important;
                border-radius: 9px !important;
                padding: 2px 6px 2px 6px !important;
                border: 1.2px solid #babbbb !important;
            }
            .stTextInput input, .stTextArea textarea, .stPassword input {
                background: #fff !important;
                color: #222 !important;
                border-radius: 7px !important;
                border: 1.5px solid #bbb !important;
                caret-color: #222 !important;
                font-size: 1.06rem !important;
                box-shadow: none !important;
            }
            .stTextInput input:focus, .stPassword input:focus {
                outline: 2px solid #6a6aee !important;
                border: 1.5px solid #6a6aee !important;
            }
            .stFileUploader, .stFileUploader > section {
                background-color: #e0e1e3 !important;
                color: #222 !important;
                border-radius: 9px !important;
            }
            .stFileUploader label, .stFileUploader span, .stFileUploader p, .stFileUploader div {
                color: #222 !important;
            }
            .stTooltipContent {
                background: #e0e1e3 !important;
                color: #222 !important;
            }
            .stAlert {
                background-color: #f6f7fa !important;
                color: #222 !important;
            }
        </style>
    """, unsafe_allow_html=True)

class DobbyChat:
    def __init__(self, api_key, model="accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new"):
        self.api_key = api_key
        self.model = model

    def chat(self, messages, **kwargs):
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "top_p": kwargs.get("top_p", 1),
            "top_k": kwargs.get("top_k", 40),
            "presence_penalty": kwargs.get("presence_penalty", 0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "temperature": kwargs.get("temperature", 0.6)
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

def send_simple_confirmation_email(to_email, company_name, role, sender_email, sender_password):
    subject = f"Selection Confirmation - {role} at {company_name}"
    body = f"""Hello,

Congratulations! You've been selected for the {role.replace('_', ' ').title()} position at {company_name}.
We will share the interview details with you soon.

Best,
From Team
"""
    return send_email(sender_email, sender_password, to_email, subject, body)

def send_interview_email(to_email, company_name, role, sender_email, sender_password, interview_datetime_ist, candidate_email, zoom_join_url):
    subject = f"Interview Scheduled - {role.replace('_', ' ').title()} at {company_name}"
    ist_time = interview_datetime_ist.strftime('%Y-%m-%d %H:%M IST')
    est_time = (interview_datetime_ist.astimezone(pytz.timezone('US/Eastern'))).strftime('%Y-%m-%d %H:%M EST')

    body = f"""Hello,

We're excited to confirm your interview for the {role.replace('_', ' ').title()} position at {company_name}. Please find the details below:

------------------------------------------------------------
Meeting Details

Title: {role.replace('_', ' ').title()} Technical Interview
Date: {interview_datetime_ist.strftime('%Y-%m-%d')}
Time: {ist_time} (Indian Standard Time) / {est_time} (Eastern Standard Time)
Duration: 60 minutes
Attendee: {candidate_email}

Location: Zoom Meeting
Zoom Link: {zoom_join_url}

Description: This meeting is a technical interview for the {role.replace('_', ' ').title()} position. Please ensure you have access to Zoom and a reliable internet connection prior to the meeting. 

We recommend joining the meeting 5 minutes early to address any potential connectivity issues and to be all set for the interview.

Time Zone Information:
- IST is UTC+5:30
- EST is UTC-5:00

For your convenience, you can convert the meeting time to your local time using this time zone converter: https://www.timeanddate.com/worldclock/converter.html

Prepare well and be confident—you got this! If you have any questions or preferences, feel free to let us know.

Best,
From Team
------------------------------------------------------------
"""
    return send_email(sender_email, sender_password, to_email, subject, body)

def send_rejection_email(to_email, role, company_name, feedback, sender_email, sender_password):
    subject = f"Your Application for {role.replace('_', ' ').title()} at {company_name}"
    body = f"""Hi,

Thank you so much for your interest in the {role.replace('_', ' ').title()} position at {company_name}. We truly appreciate the time you took to apply and we're excited to consider your application.

{feedback}

We encourage you to continue upskilling in these areas and try again in the future. Some useful resources to get you started include:
1. Coursera and edx have a wide range of courses on backend/frontend/ai-ml technologies.
2. Platforms like Udemy offer valuable tutorials on kubernetes, docker, and more.
3. Consider checking out documentation and free resources on dev.to that cover various ci/cd practices.

Keep pushing forward; your experience is an excellent foundation to build upon.

Best Regards,
From team
"""
    return send_email(sender_email, sender_password, to_email, subject, body)

def send_email(sender_email, sender_password, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def get_zoom_access_token(account_id, client_id, client_secret):
    url = "https://zoom.us/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "account_credentials",
        "account_id": account_id
    }
    try:
        response = requests.post(url, headers=headers, data=data, auth=(client_id, client_secret))
        response.raise_for_status()
        token_info = response.json()
        return token_info["access_token"]
    except Exception as e:
        st.error(f"Failed to get Zoom access token: {e}")
        return None

def schedule_zoom_meeting(access_token, topic, start_time, duration_minutes=60, timezone="Asia/Kolkata"):
    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "topic": topic,
        "type": 2,
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration": duration_minutes,
        "timezone": timezone,
        "agenda": topic,
        "settings": {
            "join_before_host": True,
            "waiting_room": False
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        meeting_info = response.json()
        return meeting_info["join_url"]
    except Exception as e:
        st.error(f"Failed to schedule Zoom meeting: {e}")
        return None

ROLE_REQUIREMENTS: Dict[str, str] = {
    "AI_ML_Engineer": """
**Required Skills:**
- Strong Python programming
- Experience with ML libraries (PyTorch or TensorFlow)
- Building and evaluating machine learning models
- Understanding of deep learning concepts (CNNs, RNNs, transformers)
- Data cleaning, feature engineering
- Deploying models into production (MLOps tools)
- Familiarity with prompt engineering and LLMs
""",
    "Frontend_Engineer": """
**Required Skills:**
- Proficient in React.js, Vue.js, or Angular
- HTML5, CSS3, and modern JavaScript/TypeScript
- Building responsive, cross-browser web apps
- State management (Redux, Pinia, or Context API)
- Frontend testing (Jest, React Testing Library)
- API integration and UI optimization
""",
    "Backend_Engineer": """
**Required Skills:**
- Python, Node.js, or Java backend development
- REST API & microservices design
- Database schema design (SQL and NoSQL)
- Authentication, security, and data validation
- Cloud deployment (AWS, GCP, or Azure)
- CI/CD pipelines and Docker
""",
    "Web_Developer": """
**Required Skills:**
- HTML5, CSS3, and modern JavaScript
- Experience with at least one JS framework (React, Vue, or Angular)
- Responsive layout & cross-browser compatibility
- Consuming APIs and AJAX/Fetch/GraphQL
- Basic backend (Node.js, Python, or PHP) is a plus
- Version control (Git)
""",
    "Web_Designer": """
**Required Skills:**
- UI/UX fundamentals for web and mobile
- Proficient in Figma, Adobe XD, or Sketch
- HTML/CSS for rapid prototyping
- Creating wireframes and mockups
- Understanding color, typography, and layout
- Handoff to developers
""",
    "JavaScript_Developer": """
**Required Skills:**
- Advanced JavaScript (ES6+)
- DOM manipulation, events, and browser APIs
- Working with Node.js and npm
- Building SPAs with frameworks (React, Vue, Angular)
- Asynchronous programming (Promises, async/await)
- Unit testing and debugging
""",
    "Full_Stack_Engineer": """
**Required Skills:**
- Proficient in both frontend (React, Vue, Angular) and backend (Node.js, Python, Java) technologies
- REST API and database design
- Authentication and security best practices
- Deploying full stack apps (Vercel, Netlify, Heroku, or AWS)
- Git and CI/CD workflows
- Understanding of DevOps and Docker is a plus
""",
    "UI_Developer": """
**Required Skills:**
- Expert in HTML5, CSS3 (Flexbox, Grid)
- CSS preprocessors (Sass/Less) and frameworks (Bootstrap, Tailwind)
- Building pixel-perfect, accessible UIs
- Animation with CSS or JS libraries (GSAP, Framer Motion)
- Optimizing for performance and mobile
"""
}

def init_session_state() -> None:
    defaults = {
        'candidate_email': "", 'dobby_api_key': "", 'resume_text': "", 'analysis_complete': False,
        'is_selected': False, 'zoom_account_id': "", 'zoom_client_id': "", 'zoom_client_secret': "",
        'email_sender': "", 'email_passkey': "", 'company_name': "", 'current_pdf': None, 'analysis_feedback': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def analyze_resume_dobby(resume_text: str, role: str, api_key: str, company_name: str) -> Tuple[bool, str]:
    dobby = DobbyChat(api_key)
    system_message = (
        f"You are an expert technical recruiter for {company_name}. "
        "Analyze resumes for technical roles and decide if a candidate should be selected."
    )
    prompt = f"""Analyze this resume for the "{role.replace("_", " ")}" position using the requirements below and return your response in valid JSON:

{ROLE_REQUIREMENTS[role]}

Resume:
{resume_text}

Response format (JSON only, no markdown, no extra text!):
{{
  "selected": true/false,
  "feedback": "Explain your decision concisely.",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "experience_level": "junior/mid/senior"
}}
"""
    messages = [{"role": "system", "content": system_message},
                {"role": "user", "content": prompt}]
    try:
        result_text = dobby.chat(messages)
        result = json.loads(result_text.strip())
        if not isinstance(result, dict) or not all(k in result for k in ["selected", "feedback"]):
            raise ValueError("Invalid response format")
        return result["selected"], result["feedback"]
    except Exception as e:
        st.error(f"Error processing response from Dobby 70B: {str(e)}\n\nRaw: {result_text if 'result_text' in locals() else ''}")
        return False, f"Error analyzing resume: {str(e)}"

def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error extracting PDF text: {str(e)}")
        return ""

def modern_sidebar():
    st.sidebar.image("logo.png", width=120)
    st.sidebar.markdown("## Configuration")
    st.sidebar.markdown("### Dobby Settings")
    api_key = st.sidebar.text_input("Dobby 70B API Key", type="password", value=st.session_state.dobby_api_key)
    st.sidebar.markdown("### Zoom Settings")
    zoom_account_id = st.sidebar.text_input("Zoom Account ID", type="password", value=st.session_state.zoom_account_id)
    zoom_client_id = st.sidebar.text_input("Zoom Client ID", type="password", value=st.session_state.zoom_client_id)
    zoom_client_secret = st.sidebar.text_input("Zoom Client Secret", type="password", value=st.session_state.zoom_client_secret)
    st.sidebar.markdown("### Email Settings")
    email_sender = st.sidebar.text_input("Sender Email", value=st.session_state.email_sender)
    email_passkey = st.sidebar.text_input("Email App Password", type="password", value=st.session_state.email_passkey)
    company_name = st.sidebar.text_input("Company Name", value=st.session_state.company_name)
    st.session_state.dobby_api_key = api_key
    st.session_state.zoom_account_id = zoom_account_id
    st.session_state.zoom_client_id = zoom_client_id
    st.session_state.zoom_client_secret = zoom_client_secret
    st.session_state.email_sender = email_sender
    st.session_state.email_passkey = email_passkey
    st.session_state.company_name = company_name

def main():
    set_modern_style()
    init_session_state()
    modern_sidebar()

    st.markdown("<h1 style='color:#222;'>DOBBY Automated Recruitment System</h1>", unsafe_allow_html=True)
    ROLES = list(ROLE_REQUIREMENTS.keys())

    required_configs = {
        'Dobby 70B API Key': st.session_state.dobby_api_key,
        'Zoom Account ID': st.session_state.zoom_account_id,
        'Zoom Client ID': st.session_state.zoom_client_id,
        'Zoom Client Secret': st.session_state.zoom_client_secret,
        'Email Sender': st.session_state.email_sender,
        'Email Password': st.session_state.email_passkey,
        'Company Name': st.session_state.company_name
    }

    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        st.info(f"Please configure the following in the sidebar: {', '.join(missing_configs)}")
        return

    if not st.session_state.dobby_api_key:
        st.info("Please enter your Dobby 70B API key in the sidebar to continue.")
        return

    role = st.selectbox("Select the role you're applying for:", ROLES)
    with st.expander("View Required Skills", expanded=True):
        st.markdown(ROLE_REQUIREMENTS[role])

    if st.button("📝 New Application"):
        keys_to_clear = [
            'resume_text', 'analysis_complete', 'is_selected', 'candidate_email', 'current_pdf', 'analysis_feedback'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                st.session_state[key] = None if key == 'current_pdf' else ""
        st.rerun()

    resume_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="resume_uploader")
    if resume_file is not None and resume_file != st.session_state.get('current_pdf'):
        st.session_state.current_pdf = resume_file
        st.session_state.resume_text = ""
        st.session_state.analysis_complete = False
        st.session_state.is_selected = False
        st.session_state.analysis_feedback = ""
        st.rerun()

    if resume_file:
        st.subheader("Uploaded Resume")
        col1, col2 = st.columns([4, 1])
        with col1:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(resume_file.read())
                tmp_file_path = tmp_file.name
            resume_file.seek(0)
            try:
                pdf_viewer(tmp_file_path)
            finally:
                os.unlink(tmp_file_path)
        with col2:
            st.download_button(label="📥 Download", data=resume_file, file_name=resume_file.name, mime="application/pdf")
        if not st.session_state.resume_text:
            with st.spinner("Processing your resume..."):
                resume_text = extract_text_from_pdf(resume_file)
                if resume_text:
                    st.session_state.resume_text = resume_text
                    st.success("Resume processed successfully!")
                else:
                    st.error("Could not process the PDF. Please try again.")

    email = st.text_input("Candidate's email address", value=st.session_state.candidate_email, key="email_input")
    st.session_state.candidate_email = email

    if st.session_state.resume_text and email and not st.session_state.analysis_complete:
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing your resume..."):
                is_selected, feedback = analyze_resume_dobby(
                    st.session_state.resume_text,
                    role,
                    st.session_state.dobby_api_key,
                    st.session_state.company_name
                )
                st.session_state.analysis_feedback = feedback
                if is_selected:
                    st.success("Congratulations! Your skills match our requirements.")
                    st.session_state.analysis_complete = True
                    st.session_state.is_selected = True
                    st.rerun()
                else:
                    st.warning("Unfortunately, your skills don't match our requirements.")
                    st.write(f"Feedback: {feedback}")
                    send_rejection_email(
                        to_email=st.session_state.candidate_email,
                        role=role,
                        company_name=st.session_state.company_name,
                        feedback=feedback,
                        sender_email=st.session_state.email_sender,
                        sender_password=st.session_state.email_passkey
                    )
                    st.info("Rejection feedback sent to candidate.")

    if st.session_state.get('analysis_complete') and st.session_state.get('is_selected', False):
        st.success("Congratulations! Your skills match our requirements.")
        st.info("Click 'Proceed with Application' to continue with the interview process.")

        if st.button("Proceed with Application", key="proceed_button"):
            with st.spinner("Sending confirmation and scheduling interview on Zoom..."):
                confirmation_sent = send_simple_confirmation_email(
                    to_email=st.session_state.candidate_email,
                    company_name=st.session_state.company_name,
                    role=role,
                    sender_email=st.session_state.email_sender,
                    sender_password=st.session_state.email_passkey
                )
                ist_tz = pytz.timezone('Asia/Kolkata')
                interview_datetime_ist = ist_tz.localize(datetime.now() + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
                zoom_token = get_zoom_access_token(
                    st.session_state.zoom_account_id,
                    st.session_state.zoom_client_id,
                    st.session_state.zoom_client_secret
                )
                zoom_join_url = None
                if zoom_token:
                    topic = f"{role.replace('_', ' ').title()} Technical Interview"
                    zoom_join_url = schedule_zoom_meeting(
                        zoom_token,
                        topic,
                        interview_datetime_ist
                    )
                if not zoom_join_url:
                    zoom_join_url = "https://zoom.us/j/your_meeting_id_here (failed to auto-schedule - please create manually!)"
                interview_sent = send_interview_email(
                    to_email=st.session_state.candidate_email,
                    company_name=st.session_state.company_name,
                    role=role,
                    sender_email=st.session_state.email_sender,
                    sender_password=st.session_state.email_passkey,
                    interview_datetime_ist=interview_datetime_ist,
                    candidate_email=st.session_state.candidate_email,
                    zoom_join_url=zoom_join_url
                )
                if confirmation_sent and interview_sent:
                    st.success("Application successfully processed! Confirmation and Zoom interview details sent.")
                else:
                    st.error("Processed, but failed to send confirmation/interview email(s). Check your credentials.")

    if st.sidebar.button("Reset Application"):
        for key in list(st.session_state.keys()):
            if key != 'dobby_api_key':
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
