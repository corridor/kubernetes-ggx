import datetime
import os
import pathlib


SQLALCHEMY_DATABASE_URI = "postgresql://user:password@postgres-service:5432/genguardx"
OUTPUT_DATA_LOCATION = str(
    pathlib.Path(os.environ["CORRIDOR_HOME"]) / "data/results/{}.parquet"
)
TASK_TIME_LIMIT = datetime.timedelta(hours=20).total_seconds()
TASK_SOFT_TIME_LIMIT = datetime.timedelta(hours=20).total_seconds()

os.environ["PYSPARK_PYTHON"] = "/opt/corridor/venv/bin/python3"
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--driver-memory 2G --executor-memory 2G --master local[4] pyspark-shell"
)

SANDBOX_MODE = False
APP_PROCESSES = 1
