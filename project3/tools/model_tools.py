def recommend_models(task_type):
    if task_type == "classification":
        return [
            "Logistic Regression",
            "Random Forest",
            "XGBoost"
        ]

    if task_type == "regression":
        return [
            "Linear Regression",
            "Random Forest Regressor",
            "XGBoost Regressor"
        ]
