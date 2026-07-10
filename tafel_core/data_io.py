import io
import json
import pandas as pd


def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    raise ValueError("Unsupported file type. Use .xlsx, .xls or .csv.")


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(sheets: dict) -> bytes:
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for sheet_name, df in sheets.items():
            safe_sheet = sheet_name[:31]
            df.to_excel(writer, index=False, sheet_name=safe_sheet)

    buffer.seek(0)
    return buffer.getvalue()


def dict_to_json_bytes(d: dict) -> bytes:
    return json.dumps(d, indent=2).encode("utf-8")