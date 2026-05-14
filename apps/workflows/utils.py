from pathlib import Path


def infer_asset_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".csv":
        return "csv"
    if suffix in {".xlsx", ".xls"}:
        return "excel"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}:
        return "image"
    if suffix in {".mp3", ".wav", ".m4a"}:
        return "audio"
    if suffix in {".txt", ".md"}:
        return "text"
    return "other"
