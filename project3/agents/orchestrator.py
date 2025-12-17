import streamlit as st
from openai import OpenAI

from agents.prompts import SYSTEM_PROMPT
from tools.data_tools import inspect_dataset
from tools.model_tools import recommend_models
from tools.training_tools import train_model

# Create OpenAI client lazily inside function to avoid import-time errors
def get_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def run_agent(user_input: str):
    df = st.session_state.df

    if df is None:
        return "Please upload a dataset first."

    # ---- STEP 1: TARGET SELECTION ----
    if st.session_state.target is None:

        # User provided a valid column
        if user_input in df.columns:
            st.session_state.target = user_input
            return (
                f"Great — we'll predict **{user_input}**.\n\n"
                "Is this a **classification** or **regression** task?"
            )

        # Otherwise ask for target
        return (
            "Which column would you like to predict?\n\n"
            f"Available columns:\n{', '.join(df.columns)}"
        )

    # ---- STEP 2: TASK TYPE ----
    if st.session_state.task_type is None:
        if "class" in user_input.lower():
            st.session_state.task_type = "classification"
        elif "regress" in user_input.lower():
            st.session_state.task_type = "regression"
        else:
            return "Is this a **classification** or **regression** problem?"

        models = recommend_models(st.session_state.task_type)
        return (
            f"Got it — **{st.session_state.task_type}**.\n\n"
            "Recommended models:\n"
            f"{', '.join(models)}\n\n"
            "Which model would you like to try?"
        )

    # ---- STEP 3: MODEL TRAINING ----
    models = recommend_models(st.session_state.task_type)

    for model in models:
        if model.lower() in user_input.lower():
            try:
                results = train_model(
                    df,
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

    # Default fallback if no recognized model
    return "Tell me what you'd like to do next."
