from __future__ import annotations

import pandas as pd


class EDAService:
    def run(self, documents: list[dict]) -> dict:
        dataset = self._first_dataset(documents)
        if dataset is None:
            return {"summary": "No dataset available for EDA.", "charts": [], "confidence": 0.4}
        df = dataset["frame"]
        numeric = df.select_dtypes(include="number")
        missing = df.isna().sum().sort_values(ascending=False).head(10).to_dict()
        correlations = numeric.corr(numeric_only=True).round(3).to_dict() if not numeric.empty else {}
        outliers = {}
        for column in numeric.columns[:10]:
            q1, q3 = numeric[column].quantile([0.25, 0.75])
            iqr = q3 - q1
            outliers[column] = int(((numeric[column] < q1 - 1.5 * iqr) | (numeric[column] > q3 + 1.5 * iqr)).sum())
        return {
            "summary": f"Analyzed {dataset['name']} with {df.shape[0]} rows and {df.shape[1]} columns.",
            "columns": list(df.columns),
            "missing_values": missing,
            "outliers": outliers,
            "correlations": correlations,
            "charts": [{"type": "histogram", "columns": list(numeric.columns[:4])}],
            "confidence": 0.84,
        }

    def _first_dataset(self, documents: list[dict]):
        for doc in documents:
            try:
                if doc.get("asset_type") == "csv":
                    return {"name": doc["name"], "frame": pd.read_csv(doc["path"])}
                if doc.get("asset_type") == "excel":
                    return {"name": doc["name"], "frame": pd.read_excel(doc["path"])}
            except Exception:
                continue
        return None
