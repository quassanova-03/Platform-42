import csv
import sqlite3
from pathlib import Path


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_LIST_FILE = BASE_DIR / "Train_List.csv"
ROUTES_DIR = BASE_DIR / "Train_Routes"
DATABASE_FILE = BASE_DIR / "database" / "transport.db"


def create_database(connection):
    """Create the database tables if they do not already exist."""

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trains (
            train_number TEXT PRIMARY KEY,
            train_name TEXT NOT NULL,
            from_station TEXT NOT NULL,
            to_station TEXT NOT NULL,
            train_type TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS route_delays (
            train_number TEXT NOT NULL,
            station_order INTEGER NOT NULL,
            station_code TEXT NOT NULL,
            station_name TEXT NOT NULL,
            average_delay REAL NOT NULL,
            right_time REAL NOT NULL,
            slight_delay REAL NOT NULL,
            significant_delay REAL NOT NULL,
            cancelled_unknown REAL NOT NULL,
            PRIMARY KEY (train_number, station_order),
            FOREIGN KEY (train_number)
                REFERENCES trains(train_number)
        )
    """)

    connection.commit()


def import_trains(connection):
    """Import train information from Train_List.csv."""

    cursor = connection.cursor()

    with open(
        TRAIN_LIST_FILE,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO trains (
                    train_number,
                    train_name,
                    from_station,
                    to_station,
                    train_type
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["Train_Number"].strip(),
                row["Train_Name"].strip(),
                row["From_Station"].strip(),
                row["To_Station"].strip(),
                row["Type"].strip()
            ))

    connection.commit()


def import_routes(connection):
    """Import all train route CSV files."""

    cursor = connection.cursor()

    route_files = sorted(ROUTES_DIR.glob("*.csv"))

    total_trains = 0
    total_stations = 0

    for route_file in route_files:

        train_number = route_file.stem

        # Remove old route data for this train
        cursor.execute(
            "DELETE FROM route_delays WHERE train_number = ?",
            (train_number,)
        )

        with open(
            route_file,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            station_order = 0

            for row in reader:
                cursor.execute("""
                    INSERT INTO route_delays (
                        train_number,
                        station_order,
                        station_code,
                        station_name,
                        average_delay,
                        right_time,
                        slight_delay,
                        significant_delay,
                        cancelled_unknown
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    train_number,
                    station_order,
                    row["Station"].strip(),
                    row["Station_Name"].strip(),
                    float(row["Average_Delay(min)"]),
                    float(row["Right Time (0-15 min's)"]),
                    float(row["Slight Delay (15-60 min's)"]),
                    float(row["Significant Delay (>1 Hour)"]),
                    float(row["Cancelled/Unknown"])
                ))

                station_order += 1
                total_stations += 1

        total_trains += 1

    connection.commit()

    return total_trains, total_stations


def main():
    """Create and populate the transport database."""

    DATABASE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_FILE)

    try:
        create_database(connection)
        import_trains(connection)

        total_trains, total_stations = import_routes(
            connection
        )

        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM trains")
        train_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM route_delays")
        route_count = cursor.fetchone()[0]

        print("\n========================================")
        print("       DATABASE IMPORT COMPLETE")
        print("========================================")
        print(f"Trains in database   : {train_count}")
        print(f"Route records        : {route_count}")
        print(f"Route files processed: {total_trains}")
        print(f"Stations imported    : {total_stations}")
        print(f"Database             : {DATABASE_FILE}")
        print("========================================\n")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
