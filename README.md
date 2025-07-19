# Dobby Recruitment Agent

This Streamlit app uses a single powerful AI agent, **Dobby 70B**, to handle the entire hiring process.  
It can read resumes, evaluate skills, schedule interviews (with real Zoom links), and communicate with applicants — all in one place.  
Dobby works like a full recruitment team, but is fully automated and super easy to use.

---

## Features

- **Automated resume screening and analysis**
- **Role-specific technical evaluation** for AI/ML Engineer, Frontend Engineer, Backend Engineer
- **Professional email correspondence** (selection, rejection, interview emails)
- **Automated interview scheduling** with real Zoom links
- **Integrated feedback system** for all candidates

---

## Important: Setup Before Running

1. **Create or use a new Gmail account for the recruiter**
   - Enable 2-Step Verification and generate a [Gmail App Password](https://support.google.com/accounts/answer/185833?hl=en)
   - The App Password is a 16-digit code (use without spaces), e.g., `abcd efgh ijkl mnop` ➔ `abcdefghijklnopm`
2. **Create a Zoom account and obtain API credentials**
   - Go to the [Zoom App Marketplace](https://marketplace.zoom.us/) and create a **Server-to-Server OAuth** app
   - Get your **Account ID**, **Client ID**, **Client Secret**
   - **Add these scopes to your app:**
     - `meeting:write:invite_links:admin`
     - `meeting:write:meeting:admin`
     - `meeting:write:meeting:master`
     - `meeting:write:invite_links:master`
     - `meeting:write:open_app:admin`
     - `user:read:email:admin`
     - `user:read:list_users:admin`
     - `billing:read:user_entitlement:admin`
     - `dashboard:read:list_meeting_participants:admin`

---

## How to Run

1. **Clone the repository**

    ```bash
    git clone https://github.com/HarshBana1177/dobby-resume.git
    cd dobby-resume
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the application**

    ```bash
    streamlit run team_agent.py
    ```

4. **Configure API keys in the Streamlit sidebar**
    - Dobby 70B API key
    - Zoom Account ID, Client ID, Client Secret
    - Recruiter Gmail address and App Password

---

## What Dobby Does

- Reads and analyzes uploaded resumes (PDF)
- Automatically evaluates technical skills for selected roles
- Sends customized selection or rejection emails
- Schedules a Zoom interview for accepted candidates and emails the join link
- Provides actionable feedback for every candidate

---


*Built with ❤️*
