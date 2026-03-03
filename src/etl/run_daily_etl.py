"""Placeholder for daily ETL job.

MVP target:
1. Fetch own ad metrics from source export/API.
2. Normalize data.
3. Upsert into ads_own and ads_own_daily_metrics.
"""

from datetime import datetime


def main() -> None:
    print(f"[ETL] run_daily_etl placeholder executed at {datetime.now().isoformat()}")
    print("TODO: implement source ingestion and database upsert.")


if __name__ == "__main__":
    main()
