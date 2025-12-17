from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline


def train_model(df, target, task_type, model_name):
    X = df.drop(columns=[target])
    y = df[target]

    # Identify column types
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns
    numeric_cols = X.select_dtypes(include=["number"]).columns

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    # Select model
    if model_name == "Logistic Regression":
        model = LogisticRegression(max_iter=1000)
        metric = "accuracy"

    elif model_name == "Random Forest":
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        metric = "accuracy"

    elif model_name == "Linear Regression":
        model = LinearRegression()
        metric = "r2"

    elif model_name == "Random Forest Regressor":
        model = RandomForestRegressor(n_estimators=200, random_state=42)
        metric = "r2"

    else:
        raise ValueError("Unsupported model")

    # Build pipeline
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    if metric == "accuracy":
        return {"accuracy": accuracy_score(y_test, preds)}

    return {"r2": r2_score(y_test, preds)}
