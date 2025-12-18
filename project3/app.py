import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tools.training_tools import train_model
from tools.model_tools import recommend_models
from openai import OpenAI

st.set_page_config(page_title="Agentic ML App", layout="wide")
st.title("Agentic ML App")

client = OpenAI()  # API key via environment variable OPENAI_API_KEY

# ---- Session state initialization ----
for key in ["df", "target", "task_type", "last_model", "messages", "user_input"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "messages" else []

# ---- Upload dataset ----
uploaded_file = st.file_uploader("Upload CSV dataset", type="csv")
if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.session_state.messages = []  # reset chat history if new dataset
    st.session_state.target = None
    st.session_state.task_type = None
    st.session_state.last_model = None
    st.write("Preview of dataset:")
    st.dataframe(st.session_state.df.head())

df = st.session_state.df

# ---- Sidebar EDA ----
if df is not None:
    st.sidebar.header("Quick EDA")
    eda_option = st.sidebar.selectbox(
        "Choose EDA action",
        ["None", "Summarize stats", "Correlation matrix", "Histogram",
         "Scatter plot", "Boxplot", "Value counts", "Missing values summary"]
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

# ---- ML Tools Section ----
st.header("ML Tools")
if df is not None:
    target_col = st.selectbox("Select target column", df.columns)
    st.session_state.target = target_col

    if pd.api.types.is_numeric_dtype(df[target_col]):
        st.session_state.task_type = "regression"
    else:
        st.session_state.task_type = "classification"

    st.write(f"Detected task type: **{st.session_state.task_type}**")

    recommended_models = recommend_models(st.session_state.task_type)
    model_choice = st.selectbox("Select model", recommended_models)

    cols = st.columns(3)

    if cols[0].button("Train Model"):
        try:
            results = train_model(df, target_col, st.session_state.task_type, model_choice)
            st.session_state.last_model = model_choice
            metric_name = list(results.keys())[0]
            st.success(f"✅ {model_choice} trained! {metric_name}: {results[metric_name]:.3f}")
        except Exception as e:
            st.error(f"⚠️ Training failed: {str(e)}")

    if cols[1].button("Compare All Recommended Models"):
        comparison = []
        for model in recommended_models:
            try:
                results = train_model(df, target_col, st.session_state.task_type, model)
                metric_name = list(results.keys())[0]
                comparison.append(f"{model}: {metric_name}={results[metric_name]:.3f}")
            except Exception as e:
                comparison.append(f"{model}: ⚠️ {str(e)}")
        st.markdown("### Comparison Results")
        st.text("\n".join(comparison))

    # Hyperparameter tuning
    if st.session_state.last_model:
        st.markdown(f"### Tune Last Model: {st.session_state.last_model}")
        with st.form("tune_form"):
            hyperparams = {}
            if "Random Forest" in st.session_state.last_model:
                hyperparams["n_estimators"] = st.number_input("n_estimators", 10, 1000, 100, 10)
                hyperparams["max_depth"] = st.number_input("max_depth (None=0)", 0, 50, 0, 1)
            elif "Linear Regression" in st.session_state.last_model:
                hyperparams["fit_intercept"] = st.checkbox("fit_intercept", True)
            elif "XGBoost" in st.session_state.last_model:
                hyperparams["n_estimators"] = st.number_input("n_estimators", 10, 1000, 100, 10)
                hyperparams["learning_rate"] = st.number_input("learning_rate", 0.01, 1.0, 0.1, 0.01)

            submitted = st.form_submit_button("Tune Model")
            if submitted:
                try:
                    if "max_depth" in hyperparams and hyperparams["max_depth"] == 0:
                        hyperparams["max_depth"] = None
                    results = train_model(
                        df,
                        target_col,
                        st.session_state.task_type,
                        st.session_state.last_model,
                        **hyperparams
                    )
                    metric_name = list(results.keys())[0]
                    st.success(f"✅ {st.session_state.last_model} tuned! {metric_name}: {results[metric_name]:.3f}")
                except Exception as e:
                    st.error(f"⚠️ Tuning failed: {str(e)}")

# ---- Agentic LLM Chat Bot Section ----
st.header("Chat Bot")
st.markdown("Ask questions about your dataset, models, or hyperparameters. The bot can execute ML actions directly.")

# Display chat history below
for msg in st.session_state.messages:
    role = "You" if msg["role"] == "user" else "AI"
    st.markdown(f"**{role}:** {msg['content']}")

def handle_chat():
    user_input = st.session_state.user_input.strip()
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.user_input = ""

    df = st.session_state.get("df")
    target = st.session_state.get("target")
    task_type = st.session_state.get("task_type")
    last_model = st.session_state.get("last_model")

    if df is None:
        st.session_state.messages.append({"role": "assistant", "content": "Please upload a dataset first."})
        return

    dataset_summary = (
        f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns.\n"
        f"Columns: {', '.join(df.columns)}\n"
    )
    if target:
        dataset_summary += f"Target column: {target}\nTask type: {task_type}\n"
    if last_model:
        dataset_summary += f"Last trained model: {last_model}\n"

    system_msg = (
        "You are an AI assistant for data analysis and machine learning. "
        "Do NOT give Python code. Interpret the request and allow the app to execute functions to return results."
        f"\n\nDataset context:\n{dataset_summary}"
    )

    messages = [{"role": "system", "content": system_msg}]
    messages += st.session_state.messages

    # Call LLM for intent
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )
    reply_text = response.choices[0].message.content
    reply_lower = reply_text.lower()
    final_reply = reply_text

    recommended_models = recommend_models(task_type)

    # ---- Execute agentic actions ----
    # Train
    for model in recommended_models:
        if f"train {model.lower()}" in reply_lower:
            try:
                results = train_model(df, target, task_type, model)
                metric_name = list(results.keys())[0]
                final_reply += f"\n✅ {model} trained! {metric_name}: {results[metric_name]:.3f}"
                st.session_state.last_model = model
            except Exception as e:
                final_reply += f"\n⚠️ Training failed for {model}: {str(e)}"

    # Compare
    if "compare" in reply_lower:
        comparison = []
        for model in recommended_models:
            try:
                results = train_model(df, target, task_type, model)
                metric_name = list(results.keys())[0]
                comparison.append(f"{model}: {metric_name}={results[metric_name]:.3f}")
            except Exception as e:
                comparison.append(f"{model}: ⚠️ {str(e)}")
        final_reply += "\n\n### Comparison Results\n" + "\n".join(comparison)

    # Basic EDA
    numeric_cols = df.select_dtypes(include="number").columns
    if "correlation" in reply_lower:
        corr = df[numeric_cols].corr()
        st.dataframe(corr)
        final_reply += "\n✅ Displayed correlation matrix."
    if "histogram" in reply_lower and len(numeric_cols) > 0:
        col = numeric_cols[0]
        fig, ax = plt.subplots()
        df[col].hist(ax=ax)
        st.pyplot(fig)
        final_reply += f"\n✅ Displayed histogram of column '{col}'."
    if "scatter" in reply_lower and len(numeric_cols) >= 2:
        fig, ax = plt.subplots()
        df.plot.scatter(x=numeric_cols[0], y=numeric_cols[1], ax=ax)
        st.pyplot(fig)
        final_reply += f"\n✅ Displayed scatter plot: {numeric_cols[0]} vs {numeric_cols[1]}"

    st.session_state.messages.append({"role": "assistant", "content": final_reply})

# Chat input below conversation
st.text_input(
    "Type your message here",
    key="user_input",
    on_change=handle_chat,
    placeholder="Press Enter to send"
)
