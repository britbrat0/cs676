import streamlit as st
from openai import OpenAI

from agents.prompts import SYSTEM_PROMPT
from tools.data_tools import inspect_dataset
from tools.model_tools import recommend_models
from tools.training_tools import train_model

client = OpenAI()

def run_agent(user_input: str):
    df = st.session_state.df

    # If no dataset yet
    if df is None:
        return "Please upload a dataset first."

    # Step 1: Inspect dataset
    if st.session_state.target is None:
        summary = inspect_dataset(df)

        return (
            f"I see a dataset with {summary['num_rows']} rows and "
            f"{summary['num_columns']} columns.\n\n"
            f"Columns:\n{list(summary['columns'].keys())}\n\n"
            "Which column would you like to predict?"
        )

    # Step 2: Detect target column
    if st.session_state.target is None and user_input in df.columns:
        st.session_state.target = user_input
        return f"Great. '{user_input}' will be the target variable. Is this a classification or regression task?"

    # Step 3: Detect task type
    if st.session_state.task_type is None:
        if "class" in user_input.lower():
            st.session_state.task_type = "classification"
        elif "regress" in user_input.lower():
            st.session_state.task_type = "regression"

        if st.session_state.task_type:
            models = recommend_models(st.session_state.task_type)
            return (
                f"Got it — {st.session_state.task_type}.\n\n"
                f"I recommend these models:\n"
                f"{', '.join(models)}\n\n"
                "Which would you like to try?"
            )

    # Step 4: Train model
    models = recommend_models(st.session_state.task_type)

    for model in models:
        if model.lower() in user_input.lower():
            results = train_model(
                df,
                st.session_state.target,
                st.session_state.task_type,
                model
            )
            st.session_state.model_results[model] = results

            metric_name = list(results.keys())[0]
            return (
                f"✅ {model} trained successfully!\n\n"
                f"{metric_name}: {results[metric_name]:.3f}\n\n"
                "Would you like to try another model or tune this one?"
            )

    return "Tell me what you’d like to do next."
