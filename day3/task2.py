import mlflow
import mlflow.sklearn

from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

mlflow.set_tracking_uri("sqlite:///quiz.db")
mlflow.set_experiment("quiz-experiment")

X, y = load_iris(return_X_y=True)

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=8
)

MAX_DEPTH = 5
N_ESTIMATORS = 100

with mlflow.start_run(run_name="quiz-run"):

    # Log parameters
    mlflow.log_param("max_depth", MAX_DEPTH)
    mlflow.log_param("n_estimators", N_ESTIMATORS)

    # Train model
    model = RandomForestClassifier(
        max_depth=MAX_DEPTH,
        n_estimators=N_ESTIMATORS,
        random_state=8
    )

    model.fit(X_tr, y_tr)

    # Predictions
    y_pred = model.predict(X_te)

    # Metrics
    acc = accuracy_score(y_te, y_pred)
    f1 = f1_score(y_te, y_pred, average="weighted")

    # Log metrics
    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("f1_score", f1)

    # Log model
    mlflow.sklearn.log_model(model, "model")
