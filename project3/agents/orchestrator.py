import streamlit as st
from openai import OpenAI
import pandas as pd

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
                "Which model would you like to try, or type 'compare all' to see a quick comparison?"
            )

        return (
            "Which column would you like to predict?\n\n"
            f"Available columns:\n{', '.join(df.columns)}"
        )

    # ---- STEP 2: MODEL TRAINING OR COMPARISON ----
    models = recommend_models(st.session_state.task_type)

    # Sample large datasets to prevent freezing
    if df.shape[0] > 5000:
        df_sample = df.sample(5000, random_state=42)
    else:
        df_sample = df

    user_input_lower = user_input.lower()

    # Compare all models if user types 'compare all'
    if "compare all" in user_input_lower:
        st.info(f"Training all recommended models on {df_sample.shape[0]} rows...")
        results_list = []

        for model in models:
            try:
                res = train_model(
                    df_sample,
                    st.session_state.target,
                    st.session_state.task_type,
                    model
                )
                metric_name = list(res.keys())[0]
                results_list.append({
                    "Model": model,
                    metric_name: res[metric_name]
                })
            except Exception as e:
                results_list.append({
                    "Model": model,
                    "Error": str(e)
                })

        # Display results as a table
        results_df = pd.DataFrame(results_list)
        st.table(results_df)

        # Keep last_model as None, user can pick a model next
        st.session_state.last_model = None
        return "Here is the comparison of all recommended models."

    # ---- Determine which model to train ----
    if "tune" in user_input_lower:
        # Train last model if tuning
        if st.session_state.last_model:
            model_to_train = st.session_state.last_model
        else:
            return "⚠️ No model has been trained yet to tune. Please select a model first."
    else:
        # Check if input matches a recommended model
        model_to_train = None
        for model in models:
            if model.lower() in user_input_lower:
                model_to_train = model
                break
        if model_to_train is None:
            return "Please select a valid model from the recommended list, or type 'compare all'."

    # ---- Train the selected model ----
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
        "Would you like to try another model, tune this one, or type 'compare all' to compare all recommended models?"
    )
