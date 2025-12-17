from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from xgboost import XGBClassifier, XGBRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


def train_model(df, target, task_type, model_name):
    X = df.drop(columns=[target])
    y = df[target]

    # Identify categorical and numeric columns
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()

    # Force categoricals to string
    for col in categorical_cols:
        X[col] = X[col].astype(str)

    # Simple imputers
    numeric_imputer = SimpleImputer(strategy="mean")
    categorical_imputer = SimpleImputer(strategy="constant", fill_value="missing")

    transformers = []

    if categorical_cols:
        transformers.append(
            ("cat", Pipeline([
                ("imputer", categorical_imputer),
                ("onehot", OneHotEncoder(handle_unknown="ignore"))
            ]), categorical_cols)
        )

    if numeric_cols:
        transformers.append(
            ("num", numeric_imputer, numeric_cols)
        )

    preprocessor = ColumnTransformer(transformers=transformers)

    # Select model
    metric = None
    if model_name == "Logistic Regression":
        model = LogisticRegression(max_iter=1000)
        metric = "accuracy"
    elif model_name == "Random Forest":
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        metric = "accuracy"
    elif model_name == "XGBoost":
        model = XGBClassifier(eval_metric="logloss", use_label_encoder=False)
        metric = "accuracy"
    elif model_name == "Linear Regression":
        model = LinearRegression()
        metric = "r2"
    elif model_name == "Random Forest Regressor":
        model = RandomForestRegressor(n_estimators=200, random_state=42)
        metric = "r2"
    elif model_name == "XGBoost Regressor":
        model = XGBRegressor()
        metric = "r2"
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # Build pipeline
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Fit
    pipeline.fit(X_train, y_train)

    # Predict
    preds = pipeline.predict(X_test)

    if metric == "accuracy":
        return {"accuracy": accuracy_score(y_test, preds)}
    else:
        return {"r2": r2_score(y_test, preds)}
