from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


class AutoMLService:
    def train(self, documents: list[dict], query: str = "") -> dict:
        data = self._load(documents)
        if data is None:
            return {"summary": "No tabular dataset available for ML training.", "models": [], "confidence": 0.35}
        name, df = data
        df = df.dropna(axis=1, how="all").dropna()
        if df.shape[0] < 10 or df.shape[1] < 2:
            return {"summary": "Dataset is too small after cleaning for model training.", "models": [], "confidence": 0.45}
        target = self._choose_target(df, query)
        y = df[target]
        x = pd.get_dummies(df.drop(columns=[target]), drop_first=True)
        if x.empty:
            return {"summary": "No usable feature columns were found.", "models": [], "confidence": 0.45}
        task = "classification" if y.dtype == "object" or y.nunique() <= 20 else "regression"
        if task == "classification":
            y = LabelEncoder().fit_transform(y.astype(str))
            model = RandomForestClassifier(n_estimators=80, random_state=42)
            baseline = LogisticRegression(max_iter=500)
            metric_name = "accuracy"
        else:
            model = RandomForestRegressor(n_estimators=80, random_state=42)
            baseline = RandomForestRegressor(n_estimators=30, random_state=7)
            metric_name = "r2"
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)
        results = []
        for candidate in [model, baseline]:
            candidate.fit(x_train, y_train)
            preds = candidate.predict(x_test)
            metric = accuracy_score(y_test, preds) if task == "classification" else r2_score(y_test, preds)
            results.append({"model": candidate.__class__.__name__, metric_name: round(float(metric), 4)})
        return {"summary": f"Trained {task} models on {name} targeting {target}.", "target": target, "task": task, "models": results, "confidence": 0.82}

    def _load(self, documents: list[dict]):
        for doc in documents:
            try:
                if doc.get("asset_type") == "csv":
                    return doc["name"], pd.read_csv(doc["path"])
                if doc.get("asset_type") == "excel":
                    return doc["name"], pd.read_excel(doc["path"])
            except Exception:
                continue
        return None

    def _choose_target(self, df, query: str):
        lowered = query.lower()
        for column in df.columns:
            if column.lower() in lowered:
                return column
        return df.columns[-1]
