import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from agents.orchestrator import train_model, run_agent
from tools.model_tools import recommend_models

st.set_page_config(page_title="Agentic ML App", layout="wide")
st.title("Agentic ML App")

# ---- Session state initialization ----
for key in ["df", "target", "task_type", "last_model", "messages", "user_input"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "messages" else []

# ---- Upload dataset ----
uploaded_file = st.file_uploader("Upload CSV dataset", type="csv")
if uploaded_file:
    st.session_state.df = pd.read_csv(uploaded_file)
    st.write("Preview of dataset:")
    st.dataframe(st.session_state.df.head())

df = st.session_state.df

# ---- Sidebar: Quick EDA ----
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

# ---- ML Tools Section ----
st.header("ML Tools")

if df is not None:
    # Target column selection
    target_col = st.selectbox("Select target column", df.columns)
    st.session_state.target = target_col

    # Infer task type automatically
    if pd.api.types.is_numeric_dtype(df[target_col]):
        st.session_state.task_type = "regression"
    else:
        st.session_state.task_type = "classification"

    st.write(f"Detected task type: **{st.session_state.task_type}**")

    # Recommended models
    recommended_models = recommend_models(st.session_state.task_type)
    model_choice = st.selectbox("Select model", recommended_models)

    # Action buttons
    cols = st.columns(3)

    if cols[0].button("Train Model"):
        try:
            results = train_model(
                df,
                st.session_state.target,
                st.session_state.task_type,
                model_choice
            )
            st.session_state.last_model = model_choice
            metric_name = list(results.keys())[0]
            st.success(f"✅ {model_choice} trained successfully! {metric_name}: {results[metric_name]:.3f}")
        except Exception as e:
            st.error(f"⚠️ Training failed for {model_choice}: {str(e)}")

    if cols[1].button("Compare All Recommended Models"):
        comparison_results = []
        for model in recommended_models:
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
        st.markdown("### Comparison Results")
        st.text("\n".join(comparison_results))

    # ---- Hyperparameter Tuning Section ----
    if st.session_state.last_model:
        st.markdown(f"### Tune Last Model: {st.session_state.last_model}")
        with st.form(key="tune_form"):
            hyperparams = {}
            # Example hyperparameters by model
            if "Random Forest" in st.session_state.last_model:
                hyperparams["n_estimators"] = st.number_input("n_estimators", min_value=10, max_value=1000, value=100, step=10)
                hyperparams["max_depth"] = st.number_input("max_depth (None=0)", min_value=0, max_value=50, value=0, step=1)
            elif "Linear Regression" in st.session_state.last_model:
                hyperparams["fit_intercept"] = st.checkbox("fit_intercept", value=True)
            elif "XGBoost" in st.session_state.last_model:
                hyperparams["n_estimators"] = st.number_input("n_estimators", min_value=10, max_value=1000, value=100, step=10)
                hyperparams["learning_rate"] = st.number_input("learning_rate", min_value=0.01, max_value=1.0, value=0.1, step=0.01)

            submitted = st.form_submit_button("Tune Model")
            if submitted:
                try:
                    if "max_depth" in hyperparams and hyperparams["max_depth"] == 0:
                        hyperparams["max_depth"] = None
                    results = train_model(
                        df,
                        st.session_state.target,
                        st.session_state.task_type,
                        st.session_state.last_model,
                        **hyperparams
                    )
                    metric_name = list(results.keys())[0]
                    st.success(f"✅ {st.session_state.last_model} tuned!\n{metric_name}: {results[metric_name]:.3f}")
                except Exception as e:
                    st.error(f"⚠️ Tuning failed: {str(e)}")

# ---- Chat Bot Section ----
st.header("Chat Bot")
st.markdown(
    "Use this chat bot for guidance on EDA, model selection, hyperparameter tuning, and general questions."
)

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

# Chat input
def handle_chat():
    user_input = st.session_state.user_input.strip()
    if not user_input:
        return
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.user_input = ""

    # Call your LLM orchestrator
    response = run_agent(user_input)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.text_input(
    "Type your message here",
    key="user_input",
    on_change=handle_chat,
    placeholder="Press Enter to send"
)
