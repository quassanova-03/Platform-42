import sqlite3
import sys
from pathlib import Path


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "database" / "transport.db"


def get_train(connection, train_number):
    """Retrieve train information from the database."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            train_number,
            train_name,
            from_station,
            to_station,
            train_type
        FROM trains
        WHERE train_number = ?
    """, (train_number,))

    return cursor.fetchone()


def get_route(connection, train_number):
    """Retrieve route and delay information for a train."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            station_code,
            station_name,
            average_delay,
            right_time,
            slight_delay,
            significant_delay,
            cancelled_unknown
        FROM route_delays
        WHERE train_number = ?
        ORDER BY station_order
    """, (train_number,))

    return cursor.fetchall()


def analyze_route(routes):
    """Calculate delay statistics for a train."""

    delays = [route[2] for route in routes]

    average_delay = sum(delays) / len(delays)
    maximum_delay = max(delays)
    minimum_delay = min(delays)

    most_delayed = max(routes, key=lambda route: route[2])
    least_delayed = min(routes, key=lambda route: route[2])

    stations_over_one_hour = sum(
        1 for delay in delays if delay > 60
    )

    return {
        "average_delay": average_delay,
        "maximum_delay": maximum_delay,
        "minimum_delay": minimum_delay,
        "most_delayed": most_delayed,
        "least_delayed": least_delayed,
        "stations_over_one_hour": stations_over_one_hour
    }


def display_report(train, routes, analysis):
    """Display the train report."""

    train_number, train_name, from_station, to_station, train_type = train

    print("\n" + "=" * 60)
    print("                 TRAIN DELAY TRACKER")
    print("=" * 60)

    print(f"Train Number : {train_number}")
    print(f"Train Name   : {train_name}")
    print(f"From         : {from_station}")
    print(f"To           : {to_station}")
    print(f"Type         : {train_type}")

    print("\n" + "-" * 60)
    print(f"{'Station':<10} {'Station Name':<25} {'Avg Delay':>10}")
    print("-" * 60)

    for route in routes:
        print(
            f"{route[0]:<10} "
            f"{route[1]:<25} "
            f"{route[2]:>10.0f}"
        )

    print("-" * 60)
    print(f"Total stations: {len(routes)}")

    print("\n" + "=" * 60)
    print("                  DELAY ANALYSIS")
    print("=" * 60)

    print(f"Mean station delay : {analysis['average_delay']:.1f} min")
    print(f"Maximum delay      : {analysis['maximum_delay']:.0f} min")
    print(f"Minimum delay      : {analysis['minimum_delay']:.0f} min")

    most_delayed = analysis["most_delayed"]

    print(
        f"\nMost delayed station:\n"
        f"{most_delayed[1]} ({most_delayed[0]}) "
        f"→ {most_delayed[2]:.0f} min"
    )

    least_delayed = analysis["least_delayed"]

    print(
        f"\nLeast delayed station:\n"
        f"{least_delayed[1]} ({least_delayed[0]}) "
        f"→ {least_delayed[2]:.0f} min"
    )

    print(
        f"\nStations with >1 hour average delay: "
        f"{analysis['stations_over_one_hour']}/{len(routes)}"
    )

    print("=" * 60)


def main():
    """Main program."""

    if len(sys.argv) != 2:
        print("Usage: python3 scripts/tracker.py <train_number>")
        print("Example: python3 scripts/tracker.py 02501")
        sys.exit(1)

    train_number = sys.argv[1].strip()

    if not DATABASE_FILE.exists():
        print("ERROR: Database does not exist.")
        print("Run: python3 scripts/database.py")
        sys.exit(1)

    connection = sqlite3.connect(DATABASE_FILE)

    try:
        train = get_train(connection, train_number)

        if train is None:
            print(f"\nERROR: Train {train_number} was not found.")
            sys.exit(1)

        routes = get_route(connection, train_number)

        if not routes:
            print(
                f"\nERROR: No route data found for train "
                f"{train_number}."
            )
            sys.exit(1)

        analysis = analyze_route(routes)

        display_report(train, routes, analysis)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
