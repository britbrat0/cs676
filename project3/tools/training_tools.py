from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression

def train_model(df, target, task_type, model_name):
    X = df.drop(columns=[target])
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    if model_name == "Logistic Regression":
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        return {"accuracy": accuracy_score(y_test, preds)}

    if model_name == "Random Forest":
        model = RandomForestClassifier(n_estimators=200)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        return {"accuracy": accuracy_score(y_test, preds)}

    if model_name == "Linear Regression":
        model = LinearRegression()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        return {"r2": r2_score(y_test, preds)}

    if model_name == "Random Forest Regressor":
        model = RandomForestRegressor(n_estimators=200)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        return {"r2": r2_score(y_test, preds)}
