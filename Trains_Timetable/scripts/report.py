import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "database" / "transport.db"
REPORTS_DIR = BASE_DIR / "reports"


def get_train_summaries(connection):
    """Calculate average delay for every train."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            t.train_number,
            t.train_name,
            t.from_station,
            t.to_station,
            AVG(r.average_delay) AS average_delay
        FROM trains t
        JOIN route_delays r
            ON t.train_number = r.train_number
        GROUP BY
            t.train_number,
            t.train_name,
            t.from_station,
            t.to_station
        ORDER BY average_delay DESC
    """)

    return cursor.fetchall()


def get_total_stations(connection):
    """Count total route records."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM route_delays
    """)

    return cursor.fetchone()[0]


def get_worst_station(connection):
    """Find the station with the highest average delay."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            station_code,
            station_name,
            train_number,
            average_delay
        FROM route_delays
        ORDER BY average_delay DESC
        LIMIT 1
    """)

    return cursor.fetchone()


def generate_report(connection):
    """Generate the complete daily report."""

    train_summaries = get_train_summaries(connection)
    total_stations = get_total_stations(connection)
    worst_station = get_worst_station(connection)

    report_date = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

    lines = []

    lines.append("=" * 70)
    lines.append("                 DAILY TRAIN DELAY REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Report date       : {report_date}")
    lines.append(f"Trains analyzed   : {len(train_summaries)}")
    lines.append(f"Stations analyzed : {total_stations}")
    lines.append("")

    if worst_station:
        station_code = worst_station[0]
        station_name = worst_station[1]
        train_number = worst_station[2]
        delay = worst_station[3]

        lines.append("HIGHEST RECORDED STATION DELAY")
        lines.append("-" * 70)
        lines.append(
            f"{station_name} ({station_code})"
        )
        lines.append(
            f"Train: {train_number}"
        )
        lines.append(
            f"Average delay: {delay:.1f} minutes"
        )
        lines.append("")

    lines.append("TRAIN SUMMARY")
    lines.append("-" * 70)
    lines.append(
        f"{'Train':<10} "
        f"{'Train Name':<25} "
        f"{'Avg Delay':>12}"
    )
    lines.append("-" * 70)

    for train in train_summaries:
        train_number = train[0]
        train_name = train[1]
        average_delay = train[4]

        lines.append(
            f"{train_number:<10} "
            f"{train_name[:25]:<25} "
            f"{average_delay:>10.1f} min"
        )

    lines.append("-" * 70)
    lines.append("")
    lines.append("End of report.")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    """Generate and save the daily report."""

    if not DATABASE_FILE.exists():
        print("ERROR: Database does not exist.")
        print("Run: python3 scripts/database.py")
        return

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_FILE)

    try:
        report = generate_report(connection)

        report_date = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
        report_file = REPORTS_DIR / f"{report_date}.txt"

        with open(
            report_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(report)

        print(report)
        print()
        print(f"Report saved to: {report_file}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
