import argparse
import sqlite3
from pathlib import Path


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = BASE_DIR / "database" / "transport.db"


def connect_database():
    """Connect to the SQLite database."""

    if not DATABASE_FILE.exists():
        print("ERROR: Database does not exist.")
        print("Run: python3 scripts/database.py")
        raise SystemExit(1)

    return sqlite3.connect(DATABASE_FILE)


def show_top_trains(connection, limit):
    """Show trains with the highest average route delay."""

    cursor = connection.cursor()

    cursor.execute("""
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
    """, (limit,))

    results = cursor.fetchall()

    print("\n" + "=" * 65)
    print(f"          TOP {limit} TRAINS BY AVERAGE DELAY")
    print("=" * 65)

    print(f"{'Train':<10} {'Train Name':<30} {'Avg Delay':>12}")
    print("-" * 65)

    for train_number, train_name, avg_delay in results:
        print(
            f"{train_number:<10} "
            f"{train_name[:30]:<30} "
            f"{avg_delay:>9.1f} min"
        )

    print("-" * 65)


def show_station(connection, station_code):
    """Show delay information for all trains at a station."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT station_name
        FROM route_delays
        WHERE station_code = ?
        LIMIT 1
    """, (station_code,))

    station = cursor.fetchone()

    if station is None:
        print(f"\nERROR: Station code '{station_code}' was not found.")
        return

    station_name = station[0]

    cursor.execute("""
        SELECT
            r.train_number,
            t.train_name,
            r.average_delay,
            r.right_time,
            r.slight_delay,
            r.significant_delay,
            r.cancelled_unknown
        FROM route_delays r
        JOIN trains t
            ON r.train_number = t.train_number
        WHERE r.station_code = ?
        ORDER BY r.average_delay DESC
    """, (station_code,))

    results = cursor.fetchall()

    print("\n" + "=" * 75)
    print(f"       STATION ANALYSIS: {station_name} ({station_code})")
    print("=" * 75)

    print(
        f"{'Train':<10} "
        f"{'Train Name':<25} "
        f"{'Avg':>8} "
        f"{'Right':>8} "
        f"{'>1hr':>8}"
    )
    print("-" * 75)

    for row in results:
        (
            train_number,
            train_name,
            avg_delay,
            right_time,
            slight_delay,
            significant_delay,
            cancelled
        ) = row

        print(
            f"{train_number:<10} "
            f"{train_name[:25]:<25} "
            f"{avg_delay:>7.1f} "
            f"{right_time:>7.1f}% "
            f"{significant_delay:>7.1f}%"
        )

    print("-" * 75)
    print(f"Trains passing through station: {len(results)}")


def get_train(connection, train_number):
    """Retrieve train information."""

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


def get_train_statistics(connection, train_number):
    """Calculate statistics for one train."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            AVG(average_delay),
            AVG(right_time),
            AVG(slight_delay),
            AVG(significant_delay),
            AVG(cancelled_unknown),
            MAX(average_delay),
            MIN(average_delay),
            COUNT(*)
        FROM route_delays
        WHERE train_number = ?
    """, (train_number,))

    return cursor.fetchone()


def show_comparison(connection, train_numbers):
    """Compare multiple trains."""

    print("\n" + "=" * 85)
    print("                       TRAIN COMPARISON")
    print("=" * 85)

    print(
        f"{'Train':<10} "
        f"{'Train Name':<25} "
        f"{'Avg Delay':>11} "
        f"{'Right':>9} "
        f"{'15-60m':>9} "
        f"{'>1hr':>9} "
        f"{'Cancel':>9}"
    )

    print("-" * 85)

    for train_number in train_numbers:
        train = get_train(connection, train_number)

        if train is None:
            print(f"{train_number:<10} NOT FOUND")
            continue

        statistics = get_train_statistics(
            connection,
            train_number
        )

        if statistics[0] is None:
            print(f"{train_number:<10} NO ROUTE DATA")
            continue

        (
            avg_delay,
            right_time,
            slight_delay,
            significant_delay,
            cancelled,
            maximum_delay,
            minimum_delay,
            station_count
        ) = statistics

        print(
            f"{train_number:<10} "
            f"{train[1][:25]:<25} "
            f"{avg_delay:>9.1f} "
            f"{right_time:>8.1f}% "
            f"{slight_delay:>8.1f}% "
            f"{significant_delay:>8.1f}% "
            f"{cancelled:>8.1f}%"
        )

    print("-" * 85)


def show_network(connection):
    """Show overall network statistics."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(DISTINCT train_number),
            COUNT(*),
            AVG(average_delay),
            AVG(right_time),
            AVG(slight_delay),
            AVG(significant_delay),
            AVG(cancelled_unknown)
        FROM route_delays
    """)

    (
        train_count,
        route_count,
        average_delay,
        right_time,
        slight_delay,
        significant_delay,
        cancelled
    ) = cursor.fetchone()

    print("\n" + "=" * 55)
    print("              NETWORK ANALYSIS")
    print("=" * 55)

    print(f"Trains analyzed          : {train_count}")
    print(f"Route records            : {route_count}")
    print(f"Average station delay    : {average_delay:.1f} min")
    print()
    print(f"Right-time share         : {right_time:.1f}%")
    print(f"15-60 min delay share    : {slight_delay:.1f}%")
    print(f">1 hour delay share      : {significant_delay:.1f}%")
    print(f"Cancelled/unknown share  : {cancelled:.1f}%")

    print("=" * 55)


def show_station_rankings(connection, limit):
    """Show stations with the highest average delay."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            station_code,
            station_name,
            AVG(average_delay) AS avg_delay,
            COUNT(DISTINCT train_number) AS train_count
        FROM route_delays
        GROUP BY
            station_code,
            station_name
        HAVING COUNT(DISTINCT train_number) >= 2
        ORDER BY avg_delay DESC
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()

    print("\n" + "=" * 70)
    print(f"       TOP {limit} STATIONS BY AVERAGE DELAY")
    print("=" * 70)

    print(
        f"{'Code':<8} "
        f"{'Station Name':<30} "
        f"{'Avg Delay':>12} "
        f"{'Trains':>8}"
    )

    print("-" * 70)

    for code, name, avg_delay, train_count in results:
        print(
            f"{code:<8} "
            f"{name[:30]:<30} "
            f"{avg_delay:>9.1f} min "
            f"{train_count:>7}"
        )

    print("-" * 70)


def show_severe_delays(connection, limit):
    """Show trains with the highest average share of delays over one hour."""

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            t.train_number,
            t.train_name,
            AVG(r.significant_delay) AS severe_delay_share,
            AVG(r.average_delay) AS avg_delay
        FROM trains t
        JOIN route_delays r
            ON t.train_number = r.train_number
        GROUP BY
            t.train_number,
            t.train_name
        ORDER BY severe_delay_share DESC
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()

    print("\n" + "=" * 75)
    print(f"       TOP {limit} TRAINS BY >1 HOUR DELAY SHARE")
    print("=" * 75)

    print(
        f"{'Train':<10} "
        f"{'Train Name':<30} "
        f"{'>1hr Share':>13} "
        f"{'Avg Delay':>12}"
    )

    print("-" * 75)

    for train_number, train_name, severe_share, avg_delay in results:
        print(
            f"{train_number:<10} "
            f"{train_name[:30]:<30} "
            f"{severe_share:>10.1f}% "
            f"{avg_delay:>9.1f} min"
        )

    print("-" * 75)


def show_route(connection, train_number):
    """Show station-by-station delay progression for a train."""

    train = get_train(connection, train_number)

    if train is None:
        print(f"\nERROR: Train '{train_number}' was not found.")
        return

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            station_code,
            station_name,
            average_delay
        FROM route_delays
        WHERE train_number = ?
        ORDER BY rowid
    """, (train_number,))

    results = cursor.fetchall()

    if not results:
        print(f"\nERROR: No route data found for train '{train_number}'.")
        return

    print("\n" + "=" * 70)
    print(f"             ROUTE ANALYSIS: {train_number}")
    print("=" * 70)

    print(f"Train : {train[1]}")
    print(f"From  : {train[2]}")
    print(f"To    : {train[3]}")
    print(f"Type  : {train[4]}")

    print()
    print(f"Stations on route     : {len(results)}")

    average_delay = sum(row[2] for row in results) / len(results)

    print(f"Average station delay : {average_delay:.1f} min")

    print()
    print("-" * 70)
    print(f"{'Station':<10} {'Station Name':<30} {'Avg Delay':>15}")
    print("-" * 70)

    for station_code, station_name, delay in results:
        print(
            f"{station_code:<10} "
            f"{station_name[:30]:<30} "
            f"{delay:>11.1f} min"
        )

    print("-" * 70)

    starting_delay = results[0][2]
    ending_delay = results[-1][2]
    total_change = ending_delay - starting_delay

    print()
    print("DELAY PROGRESSION")
    print("-" * 70)

    print(f"Starting delay : {starting_delay:.1f} min")
    print(f"Ending delay   : {ending_delay:.1f} min")
    print(f"Overall change : {total_change:+.1f} min")

    changes = []

    for i in range(1, len(results)):
        previous = results[i - 1]
        current = results[i]

        change = current[2] - previous[2]

        changes.append((
            change,
            previous[0],
            current[0],
            previous[1],
            current[1]
        ))

    changes.sort(reverse=True)

    print()
    print("LARGEST DELAY INCREASES")
    print("-" * 70)

    for change, previous_code, current_code, previous_name, current_name in changes[:5]:
        print(
            f"{previous_code} → {current_code} "
            f"{change:+.1f} min"
        )

    print("-" * 70)

def main():
    """Handle command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Indian Railway Delay Analytics"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    top_parser = subparsers.add_parser(
        "top",
        help="Show trains with the highest average delay"
    )

    top_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of trains to display"
    )

    station_parser = subparsers.add_parser(
        "station",
        help="Analyze delays at a station"
    )

    station_parser.add_argument(
        "station_code",
        help="Station code, e.g. KNE"
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare multiple trains"
    )

    compare_parser.add_argument(
        "train_numbers",
        nargs="+",
        help="Train numbers to compare"
    )

    route_parser = subparsers.add_parser(
        "route",
        help="Analyze a train route station by station"
    )

    route_parser.add_argument(
        "train_number",
        help="Train number to analyze"
    )

    network_parser = subparsers.add_parser(
        "network",
        help="Show overall network statistics"
    )

    stations_parser = subparsers.add_parser(
        "stations",
        help="Rank stations by average delay"
    )

    stations_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of stations to display"
    )

    severe_parser = subparsers.add_parser(
        "severe",
        help="Rank trains by >1 hour delay share"
    )

    severe_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of trains to display"
    )

    args = parser.parse_args()

    connection = connect_database()

    try:
        if args.command == "top":
            show_top_trains(
                connection,
                args.limit
            )

        elif args.command == "station":
            show_station(
                connection,
                args.station_code.upper()
            )

        elif args.command == "compare":
            show_comparison(
                connection,
                args.train_numbers
            )

        elif args.command == "route":
            show_route(
                connection,
                args.train_number
            )

        elif args.command == "network":
            show_network(connection)

        elif args.command == "stations":
            show_station_rankings(
                connection,
                args.limit
            )

        elif args.command == "severe":
            show_severe_delays(
                connection,
                args.limit
            )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
