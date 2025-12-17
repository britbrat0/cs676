def recommend_models(task_type: str):
    """
    Return a list of recommended models based on task type.
    """
    if task_type == "classification":
        return ["Logistic Regression", "Random Forest", "XGBoost"]
    elif task_type == "regression":
        return ["Ridge", "Lasso", "Random Forest Regressor", "XGBoost Regressor"]
    else:
        raise ValueError(f"Unsupported task type: {task_type}")
