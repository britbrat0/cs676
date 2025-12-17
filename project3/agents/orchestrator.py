import streamlit as st
import pandas as pd
import re

from tools.model_tools import recommend_models
from tools.training_tools import train_model

def parse_hyperparameters(user_input: str):
    """
    Parse simple hyperparameters from user input, e.g.,
    "tune it with n_estimators=500 max_depth=10" -> {"n_estimators":500, "max_depth":10}
    """
    pattern = r"(\w+)\s*=\s*([\d.]+)"
    matches = re.findall(pattern, user_input)
    params = {}
    for key, value in matches:
        if "." in value:
            params[key] = float(value)
        else:
            params[key] = int(value)
    return params

def run_agent(user_input: str):
    df = st.session_state.df
    if df is None:
        return "Please upload a dataset first."

    if "target" not in st.session_state:
        st.session_state.target = None
    if "task_type" not in st.session_state:
        st.session_state.task_type = None
    if "last_model" not in st.session_state:
        st.session_state.last_model = None

    # STEP 1: Target selection
    if st.session_state.target is None:
        if user_input in df.columns:
            st.session_state.target = user_input
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
        return f"Which column would you like to predict?\n\nAvailable columns:\n{', '.join(df.columns)}"

    # STEP 2: Model training / tuning
    models = recommend_models(st.session_state.task_type)
    if df.shape[0] > 5000:
        df_sample = df.sample(5000, random_state=42)
    else:
        df_sample = df

    user_input_lower = user_input.lower()
    params = None

    # Compare all models
    if "compare all" in user_input_lower:
        st.info(f"Training all recommended models on {df_sample.shape[0]} rows...")
        results_list = []
        for model in models:
            try:
                res = train_model(df_sample, st.session_state.target, st.session_state.task_type, model)
                metric_name = list(res.keys())[0]
                results_list.append({"Model": model, metric_name: res[metric_name]})
            except Exception as e:
                results_list.append({"Model": model, "Error": str(e)})
        st.table(pd.DataFrame(results_list))
        st.session_state.last_model = None
        return "Here is the comparison of all recommended models."

    # Determine which model to train
    if "tune" in user_input_lower:
        if st.session_state.last_model:
            model_to_train = st.session_state.last_model
            params = parse_hyperparameters(user_input)
        else:
            return "⚠️ No model has been trained yet to tune. Please select a model first."
    else:
        model_to_train = None
        for model in models:
            if model.lower() in user_input_lower:
                model_to_train = model
                break
        if model_to_train is None:
            return "Please select a valid model from the recommended list, or type 'compare all'."

    try:
        st.info(f"Training {model_to_train} on {df_sample.shape[0]} rows...")
        results = train_model(df_sample, st.session_state.target, st.session_state.task_type, model_to_train, params=params)
    except Exception as e:
        return f"⚠️ **Training failed for {model_to_train}.**\n\nError: `{str(e)}`\n\nThis usually means the dataset needs preprocessing or the target column is incompatible with this model."

    st.session_state.last_model = model_to_train
    metric_name = list(results.keys())[0]

    return (
        f"✅ **{model_to_train} trained successfully!**\n\n"
        f"{metric_name}: **{results[metric_name]:.3f}**\n\n"
        "Would you like to try another model, tune this one, or type 'compare all' to compare all recommended models?"
    )
