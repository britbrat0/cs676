import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
import os
from agents.orchestrator import train_model
from tools.model_tools import recommend_models

# ---- Initialize OpenAI client securely ----
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="Agentic ML Chat", layout="wide")
st.title("Agentic ML Chat with EDA & ML")

# ---- Session state ----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "target" not in st.session_state:
    st.session_state.target = None
if "task_type" not in st.session_state:
    st.session_state.task_type = None
if "last_model" not in st.session_state:
    st.session_state.last_model = None

# ---- File upload ----
uploaded_file = st.file_uploader("Upload CSV dataset", type="csv")
if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.write("Preview of dataset:")
    st.dataframe(st.session_state.df.head())

df = st.session_state.df

# ---- Sidebar for quick EDA ----
if df is not None:
    st.sidebar.header("Quick EDA Tools")
    eda_option = st.sidebar.selectbox(
        "Choose EDA action",
        [
            "None",
            "Summarize stats",
            "Correlation matrix",
            "Filter rows",
            "Histogram",
            "Scatter plot",
            "Boxplot",
            "Value counts",
            "Missing values summary"
        ]
    )

    numeric_cols = df.select_dtypes(include="number").columns

    if eda_option != "None":
        if eda_option == "Summarize stats":
            st.write(df.describe(include="all"))

        elif eda_option == "Correlation matrix":
            corr = df[numeric_cols].corr()
            st.dataframe(corr)
            fig, ax = plt.subplots()
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)

        elif eda_option == "Histogram":
            col = st.selectbox("Column for histogram", numeric_cols)
            bins = st.slider("Bins", 5, 100, 20)
            fig, ax = plt.subplots()
            df[col].hist(bins=bins, ax=ax)
            st.pyplot(fig)

        elif eda_option == "Scatter plot":
            x_col = st.selectbox("X-axis", numeric_cols)
            y_col = st.selectbox("Y-axis", numeric_cols)
            fig, ax = plt.subplots()
            df.plot.scatter(x=x_col, y=y_col, ax=ax)
            st.pyplot(fig)

        elif eda_option == "Boxplot":
            col = st.selectbox("Column for boxplot", numeric_cols)
            fig, ax = plt.subplots()
            sns.boxplot(y=df[col], ax=ax)
            st.pyplot(fig)

        elif eda_option == "Value counts":
            col = st.selectbox("Column", df.columns)
            st.write(df[col].value_counts())

        elif eda_option == "Missing values summary":
            st.write(df.isnull().sum())

# ---- Display chat history (below EDA) ----
st.markdown("### Conversation with AI:")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

# ---- Chat input (below conversation) ----
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Type your message here")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ---- System prompt for LLM ----
    system_prompt = """
    You are a helpful AI data scientist assistant.
    Guide the user step-by-step:
    - Ask which column to predict
    - Determine task type (classification/regression)
    - Suggest ML models
    - Guide tuning of hyperparameters
    - Suggest EDA actions
    Respond conversationally and clearly.
    """

    # ---- Call LLM ----
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
        )
        assistant_msg = response.choices[0].message.content
    except Exception as e:
        assistant_msg = f"⚠️ Error calling LLM: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

# ---- Conversation automatically updates on rerun ----
