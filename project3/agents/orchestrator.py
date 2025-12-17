import streamlit as st
from openai import OpenAI

from agents.prompts import SYSTEM_PROMPT
from tools.data_tools import inspect_dataset
from tools.model_tools import recommend_models
from tools.training_tools import train_model

# Lazy OpenAI client
def get_client():
    return OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))


def run_agent(user_input: str):
    df = st.session_state.df

    if df is None:
        return "Please upload a dataset first."

    # Initialize session state
    if "target" not in st.session_state:
        st.session_state.target = None
    if "task_type" not in st.session_state:
        st.session_state.task_type = None
    if "last_model" not in st.session_state:
        st.session_state.last_model = None

    # ---- STEP 1: TARGET SELECTION ----
    if st.session_state.target is None:
        if user_input in df.columns:
            st.session_state.target = user_input

            # Auto-detect task type
            target_dtype = df[user_input].dtype
            if target_dtype.kind in "biufc" and df[user_input].nunique() > 20:
                st.session_state.task_type = "regression"
            elif target_dtype.kind in "biufc":
                st.session_state.task_type = "regression"
            else:
                st.session_state.task_type = "classification"

            models = recommend_models(st.session_state.task_type)

            return (
                f"Great — we'll predict **{user_input}**.\n\n"
                f"Detected task type: **{st.session_state.task_type}**.\n"
                f"Recommended models:\n{', '.join(models)}\n\n"
                "Which model would you like to try?"
            )

        return (
            "Which column would you like to predict?\n\n"
            f"Available columns:\n{', '.join(df.columns)}"
        )

    # ---- STEP 2: MODEL TRAINING ----
    models = recommend_models(st.session_state.task_type)

    # Determine which model to train
    if st.session_state.last_model and any(
        word in user_input.lower() for word in ["tune", "this one", "it"]
    ):
        model_to_train = st.session_state.last_model
    else:
        model_to_train = None
        for model in models:
            if model.lower() in user_input.lower():
                model_to_train = model
                break
        if model_to_train is None:
            return "Please select a valid model from the recommended list."

    # Sample large datasets to prevent freezing
    if df.shape[0] > 5000:
        df_sample = df.sample(5000, random_state=42)
    else:
        df_sample = df

    try:
        st.info(f"Training {model_to_train} on {df_sample.shape[0]} rows...")
        results = train_model(
            df_sample,
            st.session_state.target,
            st.session_state.task_type,
            model_to_train
        )
    except Exception as e:
        return (
            f"⚠️ **Training failed for {model_to_train}.**\n\n"
            f"Error: `{str(e)}`\n\n"
            "This usually means the dataset needs preprocessing "
            "or the target column is incompatible with this model."
        )

    # Save last model for tuning
    st.session_state.last_model = model_to_train

    metric_name = list(results.keys())[0]

    return (
        f"✅ **{model_to_train} trained successfully!**\n\n"
        f"{metric_name}: **{results[metric_name]:.3f}**\n\n"
        "Would you like to try another model or tune this one?"
    )
