# app.py
import os
import logging
import json
import re
from typing import List, Optional

import streamlit as st
import openai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from prometheus_client import Counter, Histogram, start_http_server
from sqlalchemy import create_engine, Column, Integer, String, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import sentry_sdk
import streamlit_authenticator as stauth

# -------------------------
# Configuration from ENV
# -------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SENTRY_DSN = os.environ.get("SENTRY_DSN")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./personas.db")
PROMETHEUS_METRICS_PORT = int(os.environ.get("PROMETHEUS_METRICS_PORT", "8000"))
APP_NAME = os.environ.get("APP_NAME", "persona-feedback-simulator")

# Sentry (optional)
if SENTRY_DSN:
    sentry_sdk.init(SENTRY_DSN, traces_sample_rate=0.1, environment=os.environ.get("ENV", "development"))

# Prometheus metrics (expose on separate port)
REQUEST_COUNTER = Counter("app_requests_total", "Total app requests", ["endpoint", "status"])
OPENAI_LATENCY = Histogram("openai_request_latency_seconds", "OpenAI request latency seconds")
OPENAI_ERRORS = Counter("openai_errors_total", "OpenAI errors", ["type"])

# Start prometheus HTTP server (non-blocking)
start_http_server(PROMETHEUS_METRICS_PORT)

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(APP_NAME)

# -------------------------
# OpenAI config
# -------------------------
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable not set. Exiting.")
    raise RuntimeError("OPENAI_API_KEY must be set in environment variables")
openai.api_key = OPENAI_API_KEY

# -------------------------
# Database (SQLAlchemy)
# -------------------------
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Persona(Base):
    __tablename__ = "personas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    location = Column(String, nullable=True)
    tech_proficiency = Column(String, nullable=True)
    behavioral_traits = Column(Text, nullable=True)  # JSON string

Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Utility: Personas
# -------------------------
def load_personas_from_db() -> List[dict]:
    db = next(get_db())
    rows = db.query(Persona).all()
    personas = []
    for r in rows:
        traits = []
        if r.behavioral_traits:
            try:
                traits = json.loads(r.behavioral_traits)
            except Exception:
                traits = [t.strip() for t in r.behavioral_traits.split(",") if t.strip()]
        personas.append({
            "id": r.id,
            "name": r.name,
            "occupation": r.occupation,
            "location": r.location or "Unknown",
            "tech_proficiency": r.tech_proficiency or "Medium",
            "behavioral_traits": traits
        })
    return personas


def save_persona_to_db(p: dict):
    db = next(get_db())
    persona = Persona(
        name=p["name"],
        occupation=p["occupation"],
        location=p.get("location", "Unknown"),
        tech_proficiency=p.get("tech_proficiency", "Medium"),
        behavioral_traits=json.dumps(p.get("behavioral_traits", []))
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


# -------------------------
# OpenAI call with retry/backoff
# -------------------------
class OpenAITransientError(Exception):
    pass


@retry(
    retry=retry_if_exception_type((OpenAITransientError,)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(4)
)
def openai_chat_completion(messages, model="gpt-4o-mini", max_tokens=2000, temperature=0.8):
    with OPENAI_LATENCY.time():
        try:
            resp = openai.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return resp.choices[0].message.content
        except openai.error.RateLimitError as e:
            OPENAI_ERRORS.labels(type="rate_limit").inc()
            logger.warning("OpenAI rate limit: %s", str(e))
            raise OpenAITransientError from e
        except openai.error.APIError as e:
            OPENAI_ERRORS.labels(type="api_error").inc()
            logger.warning("OpenAI API error: %s", str(e))
            raise OpenAITransientError from e
        except Exception as e:
            OPENAI_ERRORS.labels(type="other").inc()
            logger.exception("OpenAI unexpected error")
            # non-retryable - rethrow
            raise


# -------------------------
# Authentication (streamlit_authenticator)
# - For production, replace with OAuth/OIDC (Auth0, Google, etc.)
# -------------------------
# Example credentials (use secrets manager in production)
secrets_users = json.loads(os.environ.get("AUTH_USERS_JSON", "[]"))  # e.g. [{"name":"admin","username":"admin","password":"hashedpw"}]
if secrets_users:
    # create credentials structure expected by streamlit_authenticator
    names = [u["name"] for u in secrets_users]
    usernames = [u["username"] for u in secrets_users]
    # You must provide hashed passwords; for demo we read plaintext (NOT FOR PROD)
    passwords = [u.get("password", "") for u in secrets_users]
    credentials = {"usernames": {usernames[i]: {"name": names[i], "password": passwords[i]} for i in range(len(usernames))}}
    authenticator = stauth.Authenticate(credentials, APP_NAME, "cookie", 3600)
    name, authentication_status, username = authenticator.login("Login", "sidebar")
else:
    # No authentication configured - restrict if running in prod
    authentication_status = True
    name = "anonymous"

if not authentication_status:
    st.error("Authentication failed. Contact admin.")
    st.stop()


# -------------------------
# Streamlit UI (main)
# -------------------------
st.set_page_config(page_title="Persona Feedback Simulator", page_icon="💬", layout="wide")
st.title("💬 Persona Feedback Simulator (Production Blueprint)")
st.markdown("This deployment uses server-side OpenAI keys, DB-backed personas, retries, logging, Sentry & Prometheus metrics.")

# Load personas from DB to session state once
if "personas" not in st.session_state:
    st.session_state.personas = load_personas_from_db()

# The rest of your original UI follows, with small modifications:
# - no API key entry in sidebar
# - persona CRUD calls to DB using save_persona_to_db / load_personas_from_db
# - use openai_chat_completion(...) wrapper for generation

# Example: simplified 'Ask Personas' flow (you can re-integrate your full UI)
question = st.text_input("Ask the personas a question")
selected = st.multiselect("Select personas", [f"{p['name']} ({p['occupation']})" for p in st.session_state.personas])

if st.button("Ask"):
    REQUEST_COUNTER.labels(endpoint="/ask", status="start").inc()
    if not question:
        st.warning("Ask something!")
    else:
        # Build messages like before
        personas = [p for p in st.session_state.personas if f"{p['name']} ({p['occupation']})" in selected]
        # minimal prompt
        messages = [
            {"role": "system", "content": "You are a facilitator."},
            {"role": "user", "content": f"Personas: {json.dumps(personas)}\nQuestion: {question}"}
        ]
        try:
            text = openai_chat_completion(messages)
            REQUEST_COUNTER.labels(endpoint="/ask", status="success").inc()
            st.markdown("**AI Response**")
            st.write(text)
        except Exception as e:
            REQUEST_COUNTER.labels(endpoint="/ask", status="error").inc()
            logger.exception("Failed to call OpenAI")
            st.error("Failed to get response. Administrators have been notified.")


# Persona creation (saved to DB)
with st.sidebar.form("new_persona_form"):
    new_name = st.text_input("Name*")
    new_occ = st.text_input("Occupation*")
    new_loc = st.text_input("Location")
    new_tech = st.selectbox("Tech proficiency", ["Low", "Medium", "High"])
    new_traits = st.text_area("Traits (comma-separated)")
    submitted = st.form_submit_button("Add Persona")
    if submitted:
        if not new_name or not new_occ:
            st.error("Name & Occupation required")
        else:
            p = {
                "name": new_name.strip(),
                "occupation": new_occ.strip(),
                "location": new_loc.strip(),
                "tech_proficiency": new_tech,
                "behavioral_traits": [t.strip() for t in new_traits.split(",") if t.strip()]
            }
            save_persona_to_db(p)
            st.success("Saved persona")
            st.experimental_rerun()
