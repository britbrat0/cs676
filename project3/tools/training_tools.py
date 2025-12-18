import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import xgboost as xgb
from sklearn.metrics import r2_score, accuracy_score

def train_model(df, target_col, task_type, model_name, **hyperparams):
    """
    Train a model on the given dataset with optional hyperparameters.
    Returns a dictionary with evaluation metric.
    """
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Convert categorical features to dummy variables
    X = pd.get_dummies(X, drop_first=True)

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Create model with hyperparameters
    if model_name == "Linear Regression":
        model = LinearRegression(**hyperparams)
    elif model_name == "Ridge":
        model = Ridge(**hyperparams)
    elif model_name == "Lasso":
        model = Lasso(**hyperparams)
    elif model_name == "Random Forest Regressor":
        model = RandomForestRegressor(**hyperparams)
    elif model_name == "Random Forest Classifier":
        model = RandomForestClassifier(**hyperparams)
    elif model_name == "Logistic Regression":
        model = LogisticRegression(max_iter=1000, **hyperparams)
    elif model_name == "XGBoost Regressor":
        model = xgb.XGBRegressor(**hyperparams)
    elif model_name == "XGBoost Classifier":
        model = xgb.XGBClassifier(**hyperparams)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # Fit the model
    model.fit(X_train, y_train)

    # Evaluate
    if task_type == "regression":
        score = r2_score(y_test, model.predict(X_test))
        return {"r2": score}
    else:
        score = accuracy_score(y_test, model.predict(X_test))
        return {"accuracy": score}
