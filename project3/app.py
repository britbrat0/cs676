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
for key in ["messages", "df", "target", "task_type", "last_model", "user_input"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "messages" else []

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

# ---- Display chat history ----
st.markdown("### Conversation with AI:")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

# ---- Chat input ----
def handle_input():
    user_input = st.session_state.user_input.strip()
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.user_input = ""  # clear input box

    # ---- ML commands ----
    if df is not None and st.session_state.target and st.session_state.task_type:
        lower_input = user_input.lower()

        # Train a specific model
        if "train" in lower_input:
            model_name = user_input.split("train")[-1].strip()
            if not model_name:
                msg = "Please specify a model to train."
            else:
                try:
                    results = train_model(
                        df,
                        st.session_state.target,
                        st.session_state.task_type,
                        model_name
                    )
                    metric_name = list(results.keys())[0]
                    st.session_state.last_model = model_name
                    msg = f"✅ {model_name} trained successfully!\n{metric_name}: {results[metric_name]:.3f}"
                except Exception as e:
                    msg = f"⚠️ Training failed for {model_name}.\nError: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": msg})
            return

        # Compare all recommended models
        elif "compare all" in lower_input:
            models = recommend_models(st.session_state.task_type)
            comparison_results = []
            for model in models:
                try:
                    results = train_model(
                        df,
                        st.session_state.target,
                        st.session_state.task_type,
                        model
                    )
                    metric_name = list(results.keys())[0]
                    comparison_results.append(f"{model}: {metric_name}={results[metric_name]:.3f}")
                except Exception as e:
                    comparison_results.append(f"{model}: ⚠️ {str(e)}")
            msg = "### Comparison Results\n" + "\n".join(comparison_results)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            return

        # Tune last trained model
        elif "tune" in lower_input:
            if st.session_state.last_model is None:
                msg = "No model trained yet to tune."
            else:
                parts = user_input.split()
                kwargs = {}
                for part in parts:
                    if "=" in part:
                        key, val = part.split("=")
                        try:
                            kwargs[key] = float(val)
                        except ValueError:
                            kwargs[key] = val
                try:
                    results = train_model(
                        df,
                        st.session_state.target,
                        st.session_state.task_type,
                        st.session_state.last_model,
                        **kwargs
                    )
                    metric_name = list(results.keys())[0]
                    msg = f"✅ {st.session_state.last_model} tuned!\n{metric_name}: {results[metric_name]:.3f}"
                except Exception as e:
                    msg = f"⚠️ Tuning failed: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": msg})
            return

    # ---- Otherwise, call LLM ----
    system_prompt = """
    You are a helpful AI data scientist assistant.
    Guide the user step-by-step:
    - Ask which column to predict
    - Determine task type
    - Suggest ML models
    - Guide tuning of hyperparameters
    - Suggest EDA actions
    Respond conversationally.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
        )
        assistant_msg = response.choices[0].message.content
    except Exception as e:
        assistant_msg = f"⚠️ Error calling LLM: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

# Input box below conversation
st.text_input(
    "Type your message here",
    key="user_input",
    on_change=handle_input,
    placeholder="Press Enter to send"
)

# ---- Dynamic ML buttons ----
if df is not None:
    if st.session_state.target is None:
        st.info("Please select the target column first (type it in chat).")
    elif st.session_state.task_type is None:
        st.info("Please specify the task type (classification or regression).")
    else:
        recommended_models = recommend_models(st.session_state.task_type)
        st.markdown("### Suggested Models:")
        cols = st.columns(len(recommended_models) + 2)

        for i, model in enumerate(recommended_models):
            if cols[i].button(f"Train {model}"):
                st.session_state.messages.append({"role": "user", "content": f"train {model}"})
                handle_input()

        if cols[len(recommended_models)].button("Compare all models"):
            st.session_state.messages.append({"role": "user", "content": "compare all"})
            handle_input()

        if cols[len(recommended_models)+1].button("Tune last model"):
            st.session_state.messages.append({"role": "user", "content": "tune"})
            handle_input()
