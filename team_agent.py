from typing import Literal, Tuple, Dict, Optional
import os
import time
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

# === Dobby ===
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

# === Email sending functions (SMTP) ===

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

# === ZOOM API INTEGRATION ===
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
        "type": 2,  # Scheduled meeting
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

# === Role requirements as a constant dictionary ===
ROLE_REQUIREMENTS: Dict[str, str] = {
    "AI_ML_Engineer": """
        Required Skills:
        - Python, PyTorch/TensorFlow
        - Machine Learning algorithms and frameworks
        - Deep Learning and Neural Networks
        - Data preprocessing and analysis
        - MLOps and model deployment
        - RAG, LLM, Finetuning and Prompt Engineering
    """,
    "Frontend_Engineer": """
        Required Skills:
        - React/Vue.js/Angular
        - HTML5, CSS3, JavaScript/TypeScript
        - Responsive design
        - State management
        - Frontend testing
    """,
    "Backend_Engineer": """
        Required Skills:
        - Python/Java/Node.js
        - REST APIs
        - Database design and management
        - System architecture
        - Cloud services (AWS/GCP/Azure)
        - Kubernetes, Docker, CI/CD
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

def analyze_resume_dobby(resume_text: str, role: Literal["AI_ML_Engineer", "Frontend_Engineer", "Backend_Engineer"], api_key: str, company_name: str) -> Tuple[bool, str]:
    dobby = DobbyChat(api_key)
    system_message = (
        f"You are an expert technical recruiter for {company_name}. "
        "Analyze resumes for technical roles and decide if a candidate should be selected."
    )
    prompt = f"""Please analyze this resume against the following requirements and provide your response in valid JSON format:
Role Requirements:
{ROLE_REQUIREMENTS[role]}
Resume Text:
{resume_text}
Your response must be a valid JSON object like this:
{{
  "selected": true/false,
  "feedback": "Detailed feedback explaining the decision",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "experience_level": "junior/mid/senior"
}}
Evaluation criteria:
1. Match at least 70% of required skills
2. Consider both theoretical knowledge and practical experience
3. Value project experience and real-world applications
4. Consider transferable skills from similar technologies
5. Look for evidence of continuous learning and adaptability
Important: Return ONLY the JSON object without any markdown formatting or backticks.
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

def main() -> None:
    st.title("Dobby Recruitment System")

    init_session_state()
    with st.sidebar:
        st.header("Configuration")
        st.subheader("Dobby Settings")
        api_key = st.text_input("Dobby 70B API Key", type="password", value=st.session_state.dobby_api_key, help="Get your API key from Fireworks/Sentient")
        if api_key: st.session_state.dobby_api_key = api_key

        st.subheader("Zoom Settings")
        zoom_account_id = st.text_input("Zoom Account ID", type="password", value=st.session_state.zoom_account_id)
        zoom_client_id = st.text_input("Zoom Client ID", type="password", value=st.session_state.zoom_client_id)
        zoom_client_secret = st.text_input("Zoom Client Secret", type="password", value=st.session_state.zoom_client_secret)
        if zoom_account_id: st.session_state.zoom_account_id = zoom_account_id
        if zoom_client_id: st.session_state.zoom_client_id = zoom_client_id
        if zoom_client_secret: st.session_state.zoom_client_secret = zoom_client_secret

        st.subheader("Email Settings")
        email_sender = st.text_input("Sender Email", value=st.session_state.email_sender, help="Email address to send from")
        email_passkey = st.text_input("Email App Password", type="password", value=st.session_state.email_passkey, help="App-specific password for email")
        company_name = st.text_input("Company Name", value=st.session_state.company_name, help="Name to use in email communications")
        if email_sender: st.session_state.email_sender = email_sender
        if email_passkey: st.session_state.email_passkey = email_passkey
        if company_name: st.session_state.company_name = company_name

        required_configs = {'Dobby 70B API Key': st.session_state.dobby_api_key,
                            'Zoom Account ID': st.session_state.zoom_account_id,
                            'Zoom Client ID': st.session_state.zoom_client_id,
                            'Zoom Client Secret': st.session_state.zoom_client_secret,
                            'Email Sender': st.session_state.email_sender, 'Email Password': st.session_state.email_passkey,
                            'Company Name': st.session_state.company_name}

    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        st.warning(f"Please configure the following in the sidebar: {', '.join(missing_configs)}")
        return

    if not st.session_state.dobby_api_key:
        st.warning("Please enter your Dobby 70B API key in the sidebar to continue.")
        return

    role = st.selectbox("Select the role you're applying for:", ["AI_ML_Engineer", "Frontend_Engineer", "Backend_Engineer"])
    with st.expander("View Required Skills", expanded=True): st.markdown(ROLE_REQUIREMENTS[role])

    if st.button("📝 New Application"):
        keys_to_clear = ['resume_text', 'analysis_complete', 'is_selected', 'candidate_email', 'current_pdf', 'analysis_feedback']
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
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(resume_file.read())
                tmp_file_path = tmp_file.name
            resume_file.seek(0)
            try: pdf_viewer(tmp_file_path)
            finally: os.unlink(tmp_file_path)
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
                    # Send the custom rejection email
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
                # Send confirmation email
                confirmation_sent = send_simple_confirmation_email(
                    to_email=st.session_state.candidate_email,
                    company_name=st.session_state.company_name,
                    role=role,
                    sender_email=st.session_state.email_sender,
                    sender_password=st.session_state.email_passkey
                )
                # Schedule interview for "tomorrow, 7:00pm IST"
                ist_tz = pytz.timezone('Asia/Kolkata')
                interview_datetime_ist = ist_tz.localize(datetime.now() + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
                # 1. Get Zoom access token
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
                # If Zoom failed, use a fallback
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
