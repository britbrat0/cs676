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

    for model in models:
        if model.lower() in user_input.lower():
            # Sample large datasets to prevent freezing
            if df.shape[0] > 5000:
                df_sample = df.sample(5000, random_state=42)
            else:
                df_sample = df

            try:
                st.info(f"Training {model} on {df_sample.shape[0]} rows...")
                results = train_model(
                    df_sample,
                    st.session_state.target,
                    st.session_state.task_type,
                    model
                )
            except Exception as e:
                return (
                    f"⚠️ **Training failed for {model}.**\n\n"
                    f"Error: `{str(e)}`\n\n"
                    "This usually means the dataset needs preprocessing "
                    "or the target column is incompatible with this model."
                )

            metric_name = list(results.keys())[0]

            return (
                f"✅ **{model} trained successfully!**\n\n"
                f"{metric_name}: **{results[metric_name]:.3f}**\n\n"
                "Would you like to try another model or tune this one?"
            )

    return "Please select a valid model from the recommended list."
