import pandas as pd
import pyodbc


CSV_PATH = "data/raw/dynamic_supply_chain_logistics_dataset.csv"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=ColdChainLogistics;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# Read CSV
df = pd.read_csv(CSV_PATH)

# Select only the fields required by our secure database layer
df = df[
    [
        "timestamp",
        "vehicle_gps_latitude",
        "vehicle_gps_longitude",
        "iot_temperature",
        "cargo_condition_status",
        "risk_classification",
        "delay_probability",
        "port_congestion_level",
        "route_risk_level",
    ]
].copy()

# Rename CSV columns to database columns
df.columns = [
    "TS_UTC",
    "V_LAT",
    "V_LON",
    "IOT_TEMP_VAL_C",
    "CGO_COND_CD",
    "RISK_CLS_TXT",
    "DELAY_PROB_DEC",
    "PRT_CNG_LVL",
    "RT_RSK_IDX",
]

# Convert timestamp
df["TS_UTC"] = pd.to_datetime(df["TS_UTC"])

# Connect to SQL Server
conn = pyodbc.connect(CONNECTION_STRING)
cursor = conn.cursor()

# Insert records
insert_query = """
INSERT INTO dbo.TBL_SC_FLEET_HIST_RAW
(
    TS_UTC,
    V_LAT,
    V_LON,
    IOT_TEMP_VAL_C,
    CGO_COND_CD,
    RISK_CLS_TXT,
    DELAY_PROB_DEC,
    PRT_CNG_LVL,
    RT_RSK_IDX,
    SYS_INGEST_FLAG
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

records = []

for _, row in df.iterrows():
    records.append(
        (
            row["TS_UTC"].to_pydatetime(),
            float(row["V_LAT"]),
            float(row["V_LON"]),
            float(row["IOT_TEMP_VAL_C"]),
            str(row["CGO_COND_CD"]),
            str(row["RISK_CLS_TXT"]),
            float(row["DELAY_PROB_DEC"]),
            float(row["PRT_CNG_LVL"]),
            float(row["RT_RSK_IDX"]),
            "Y",
        )
    )

print(f"Preparing to insert {len(records)} records...")

cursor.fast_executemany = True
cursor.executemany(insert_query, records)

conn.commit()

print(f"Successfully inserted {len(records)} records.")

cursor.close()
conn.close()

print("Database connection closed.")