from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import accuracy_score, r2_score
import pandas as pd
import numpy as np

def train_model(df, target, task_type, model_name, params=None):
    X = df.drop(columns=[target])
    y = df[target]

    # Fill missing numeric values with median
    X_numeric = X.select_dtypes(include=[np.number])
    X_numeric = X_numeric.fillna(X_numeric.median())

    # Fill missing categorical values with a placeholder
    X_categorical = X.select_dtypes(include=["object", "category"]).fillna("missing")

    # Build preprocessor
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), X_numeric.columns),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse=False), X_categorical.columns)
    ], remainder="drop")

    # Select model
    if model_name == "Logistic Regression":
        model = LogisticRegression(max_iter=1000)
        metric = "accuracy"
    elif model_name == "Random Forest":
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        metric = "accuracy"
    elif model_name == "XGBoost":
        model = XGBClassifier(eval_metric="logloss", use_label_encoder=False)
        metric = "accuracy"
    elif model_name == "Ridge":
        model = Ridge(alpha=1.0)
        metric = "r2"
    elif model_name == "Lasso":
        model = Lasso(alpha=1.0)
        metric = "r2"
    elif model_name == "Random Forest Regressor":
        model = RandomForestRegressor(n_estimators=200, random_state=42)
        metric = "r2"
    elif model_name == "XGBoost Regressor":
        model = XGBRegressor()
        metric = "r2"
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # Apply hyperparameter overrides
    if params:
        # Convert True/False strings to bool
        for k, v in params.items():
            if v in ["True", "False"]:
                params[k] = v == "True"
        model.set_params(**params)

    # Build pipeline
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train
    pipeline.fit(X_train, y_train)

    # Predict & evaluate
    y_pred = pipeline.predict(X_test)
    if metric == "accuracy":
        score = accuracy_score(y_test, y_pred)
    else:
        score = r2_score(y_test, y_pred)

    return {metric: score}
