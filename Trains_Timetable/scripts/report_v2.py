import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database" / "transport.db"
REPORTS_DIR = BASE_DIR / "reports"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect_database():
    """Connect to the SQLite database."""

    if not DATABASE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE}"
        )

    return sqlite3.connect(DATABASE)


# =========================================================
# NETWORK SUMMARY
# =========================================================

def get_network_summary(connection):

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM trains"
    )

    train_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM route_delays"
    )

    route_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT
            AVG(average_delay),
            AVG(right_time),
            AVG(slight_delay),
            AVG(significant_delay),
            AVG(cancelled_unknown)
        FROM route_delays
        """
    )

    (
        average_delay,
        right_time,
        slight_delay,
        significant_delay,
        cancelled
    ) = cursor.fetchone()

    return (
        train_count,
        route_count,
        average_delay or 0,
        right_time or 0,
        slight_delay or 0,
        significant_delay or 0,
        cancelled or 0
    )


# =========================================================
# TOP TRAINS
# =========================================================

def get_top_trains(connection, limit=10):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            t.train_number,
            t.train_name,
            AVG(r.average_delay) AS avg_delay
        FROM trains t
        JOIN route_delays r
            ON t.train_number = r.train_number
        GROUP BY
            t.train_number,
            t.train_name
        ORDER BY avg_delay DESC
        LIMIT ?
        """,
        (limit,)
    )

    return cursor.fetchall()


# =========================================================
# TOP STATIONS
# =========================================================

def get_top_stations(connection, limit=10):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            r.station_code,
            r.station_name,
            AVG(r.average_delay) AS avg_delay,
            COUNT(DISTINCT r.train_number) AS train_count
        FROM route_delays r
        GROUP BY
            r.station_code,
            r.station_name
        HAVING COUNT(DISTINCT r.train_number) >= 2
        ORDER BY avg_delay DESC
        LIMIT ?
        """,
        (limit,)
    )

    return cursor.fetchall()


# =========================================================
# SEVERE DELAY TRAINS
# =========================================================

def get_severe_trains(connection, limit=10):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            t.train_number,
            t.train_name,
            AVG(r.significant_delay) AS severe_share,
            AVG(r.average_delay) AS avg_delay
        FROM trains t
        JOIN route_delays r
            ON t.train_number = r.train_number
        GROUP BY
            t.train_number,
            t.train_name
        ORDER BY severe_share DESC
        LIMIT ?
        """,
        (limit,)
    )

    return cursor.fetchall()


# =========================================================
# ROUTE DELAY INCREASES
# =========================================================

def get_route_increases(connection, limit=10):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            train_number,
            station_code,
            station_name,
            average_delay
        FROM route_delays
        ORDER BY
            train_number,
            rowid
        """
    )

    rows = cursor.fetchall()

    increases = []

    current_train = None
    previous = None

    for row in rows:

        (
            train_number,
            station_code,
            station_name,
            delay
        ) = row

        if train_number != current_train:

            current_train = train_number
            previous = None

        if previous is not None:

            (
                previous_code,
                previous_name,
                previous_delay
            ) = previous

            increase = delay - previous_delay

            if increase > 0:

                increases.append(
                    (
                        increase,
                        train_number,
                        previous_code,
                        station_code,
                        previous_name,
                        station_name
                    )
                )

        previous = (
            station_code,
            station_name,
            delay
        )

    increases.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return increases[:limit]


# =========================================================
# REPORT GENERATION
# =========================================================

def generate_report():

    connection = connect_database()

    try:

        # Use Indian Standard Time.

        now = datetime.now(
            ZoneInfo("Asia/Kolkata")
        )

        report_date = now.strftime(
            "%Y-%m-%d"
        )

        report_time = now.strftime(
            "%H:%M:%S"
        )

        # Gather all analytics.

        (
            train_count,
            route_count,
            average_delay,
            right_time,
            slight_delay,
            severe_delay,
            cancelled
        ) = get_network_summary(
            connection
        )

        top_trains = get_top_trains(
            connection
        )

        top_stations = get_top_stations(
            connection
        )

        severe_trains = get_severe_trains(
            connection
        )

        route_increases = get_route_increases(
            connection
        )

        lines = []

        # =================================================
        # HEADER
        # =================================================

        lines.append(
            "=" * 72
        )

        lines.append(
            "                    DAILY TRAIN DELAY REPORT"
        )

        lines.append(
            "=" * 72
        )

        lines.append("")

        lines.append(
            f"Report date : {report_date}"
        )

        lines.append(
            f"Generated   : {report_time} IST"
        )

        lines.append("")

        # =================================================
        # NETWORK SUMMARY
        # =================================================

        lines.append(
            "NETWORK SUMMARY"
        )

        lines.append(
            "-" * 72
        )

        lines.append(
            f"Trains analyzed        : {train_count}"
        )

        lines.append(
            f"Route records          : {route_count}"
        )

        lines.append(
            f"Average station delay  : "
            f"{average_delay:.1f} min"
        )

        lines.append(
            f"Right-time share       : "
            f"{right_time:.1f}%"
        )

        lines.append(
            f"15-60 min delay share  : "
            f"{slight_delay:.1f}%"
        )

        lines.append(
            f">1 hour delay share    : "
            f"{severe_delay:.1f}%"
        )

        lines.append(
            f"Cancelled/unknown      : "
            f"{cancelled:.1f}%"
        )

        lines.append("")

        # =================================================
        # TOP TRAINS
        # =================================================

        lines.append(
            "TOP 10 TRAINS BY AVERAGE DELAY"
        )

        lines.append(
            "-" * 72
        )

        lines.append(
            f"{'Train':<10}"
            f"{'Train Name':<32}"
            f"{'Avg Delay':>15}"
        )

        lines.append(
            "-" * 72
        )

        for (
            train_number,
            train_name,
            avg_delay
        ) in top_trains:

            lines.append(
                f"{train_number:<10}"
                f"{train_name[:30]:<32}"
                f"{avg_delay:>11.1f} min"
            )

        lines.append("")

        # =================================================
        # TOP STATIONS
        # =================================================

        lines.append(
            "TOP 10 STATIONS BY AVERAGE DELAY"
        )

        lines.append(
            "-" * 72
        )

        lines.append(
            f"{'Code':<8}"
            f"{'Station':<28}"
            f"{'Avg Delay':>15}"
            f"{'Trains':>10}"
        )

        lines.append(
            "-" * 72
        )

        for (
            station_code,
            station_name,
            avg_delay,
            trains
        ) in top_stations:

            lines.append(
                f"{station_code:<8}"
                f"{station_name[:26]:<28}"
                f"{avg_delay:>11.1f} min"
                f"{trains:>10}"
            )

        lines.append("")

        # =================================================
        # SEVERE DELAYS
        # =================================================

        lines.append(
            "TOP TRAINS BY >1 HOUR DELAY SHARE"
        )

        lines.append(
            "-" * 72
        )

        lines.append(
            f"{'Train':<10}"
            f"{'Train Name':<32}"
            f"{'>1hr Share':>15}"
            f"{'Avg Delay':>15}"
        )

        lines.append(
            "-" * 72
        )

        for (
            train_number,
            train_name,
            severe_share,
            avg_delay
        ) in severe_trains:

            lines.append(
                f"{train_number:<10}"
                f"{train_name[:30]:<32}"
                f"{severe_share:>11.1f}%"
                f"{avg_delay:>12.1f} min"
            )

        lines.append("")

        # =================================================
        # ROUTE DELAY ACCUMULATION
        # =================================================

        lines.append(
            "LARGEST DELAY INCREASES ALONG ROUTES"
        )

        lines.append(
            "-" * 72
        )

        lines.append(
            f"{'Train':<10}"
            f"{'Route':<20}"
            f"{'Increase':>15}"
        )

        lines.append(
            "-" * 72
        )

        for (
            increase,
            train_number,
            previous_code,
            current_code,
            previous_name,
            current_name
        ) in route_increases:

            route = (
                f"{previous_code}"
                f" -> "
                f"{current_code}"
            )

            lines.append(
                f"{train_number:<10}"
                f"{route:<20}"
                f"{increase:>11.1f} min"
            )

        lines.append("")

        # =================================================
        # FOOTER
        # =================================================

        lines.append(
            "End of report."
        )

        lines.append(
            "=" * 72
        )

        report_text = "\n".join(lines)

        print(report_text)

        # Save report.

        REPORTS_DIR.mkdir(
            exist_ok=True
        )

        report_file = (
            REPORTS_DIR
            / f"{report_date}.txt"
        )

        report_file.write_text(
            report_text + "\n",
            encoding="utf-8"
        )

        print(
            f"\nReport saved to: "
            f"{report_file}"
        )

    finally:

        connection.close()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    try:

        generate_report()

    except Exception as error:

        print(
            f"ERROR: Report generation failed: "
            f"{error}"
        )

        raise
