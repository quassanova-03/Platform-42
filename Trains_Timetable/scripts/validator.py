import csv
import re
import sys
from pathlib import Path


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_LIST_FILE = BASE_DIR / "Train_List.csv"
ROUTES_DIR = BASE_DIR / "Train_Routes"


# =========================================================
# EXPECTED CSV COLUMNS
# =========================================================

TRAIN_LIST_COLUMNS = {
    "train_number",
    "train_name",
    "from_station",
    "to_station",
    "type"
}

ROUTE_COLUMNS = {
    "station",
    "station_name",
    "average_delay_min",
    "right_time_0_15_min_s",
    "slight_delay_15_60_min_s",
    "significant_delay_1_hour",
    "cancelled_unknown"
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def normalize_header(header):
    """Convert a CSV header into a consistent format."""

    header = header.strip().lower()

    header = re.sub(
        r"[^a-z0-9]+",
        "_",
        header
    )

    return header.strip("_")


def read_csv(path):
    """Read a CSV file and return normalized headers and rows."""

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("CSV has no header")

        headers = {
            normalize_header(header): header
            for header in reader.fieldnames
        }

        rows = list(reader)

    return headers, rows


def parse_number(value, field_name):
    """Convert a value into a number."""

    try:
        return float(value.strip())

    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid numeric value for {field_name}: '{value}'"
        )


def valid_train_number(value):
    """Check whether a train number contains digits only."""

    return bool(
        re.fullmatch(
            r"\d+",
            value.strip()
        )
    )


# =========================================================
# TRAIN LIST VALIDATION
# =========================================================

def validate_train_list():
    """Validate Train_List.csv."""

    print("\nTRAIN LIST VALIDATION")
    print("-" * 55)

    errors = []
    warnings = []

    if not TRAIN_LIST_FILE.exists():

        errors.append(
            f"Missing file: {TRAIN_LIST_FILE}"
        )

        return errors, warnings, set()

    try:

        headers, rows = read_csv(
            TRAIN_LIST_FILE
        )

    except Exception as error:

        errors.append(
            f"Could not read Train_List.csv: {error}"
        )

        return errors, warnings, set()

    missing_columns = (
        TRAIN_LIST_COLUMNS - set(headers)
    )

    if missing_columns:

        errors.append(
            "Missing Train_List columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    if errors:

        return errors, warnings, set()

    train_numbers = set()

    for row_number, row in enumerate(
        rows,
        start=2
    ):

        train_number = row[
            headers["train_number"]
        ].strip()

        train_name = row[
            headers["train_name"]
        ].strip()

        from_station = row[
            headers["from_station"]
        ].strip()

        to_station = row[
            headers["to_station"]
        ].strip()

        train_type = row[
            headers["type"]
        ].strip()

        if not train_number:

            errors.append(
                f"Row {row_number}: "
                "missing train number"
            )

            continue

        if not valid_train_number(
            train_number
        ):

            errors.append(
                f"Row {row_number}: "
                f"invalid train number "
                f"'{train_number}'"
            )

        if train_number in train_numbers:

            errors.append(
                f"Row {row_number}: "
                f"duplicate train number "
                f"'{train_number}'"
            )

        train_numbers.add(
            train_number
        )

        if not train_name:

            errors.append(
                f"Row {row_number}: "
                "missing train name"
            )

        if not from_station:

            errors.append(
                f"Row {row_number}: "
                "missing origin station"
            )

        if not to_station:

            errors.append(
                f"Row {row_number}: "
                "missing destination station"
            )

        if not train_type:

            warnings.append(
                f"Row {row_number}: "
                "missing train type"
            )

    print(
        "File found              : YES"
    )

    print(
        f"Train records           : {len(rows)}"
    )

    print(
        f"Unique train numbers    : "
        f"{len(train_numbers)}"
    )

    print(
        "Required columns        : OK"
    )

    return (
        errors,
        warnings,
        train_numbers
    )


# =========================================================
# ROUTE FILE VALIDATION
# =========================================================

def validate_route_file(path):
    """Validate one train route CSV."""

    errors = []
    warnings = []

    try:

        headers, rows = read_csv(path)

    except Exception as error:

        errors.append(
            f"{path.name}: "
            f"could not read file: {error}"
        )

        return errors, warnings, 0

    missing_columns = (
        ROUTE_COLUMNS - set(headers)
    )

    if missing_columns:

        errors.append(
            f"{path.name}: "
            "missing columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

        return errors, warnings, 0

    if not rows:

        errors.append(
            f"{path.name}: "
            "file contains no route records"
        )

        return errors, warnings, 0

    valid_rows = 0

    for row_number, row in enumerate(
        rows,
        start=2
    ):

        try:

            station = row[
                headers["station"]
            ].strip()

            station_name = row[
                headers["station_name"]
            ].strip()

            if not station:

                raise ValueError(
                    "missing station code"
                )

            if not station_name:

                raise ValueError(
                    "missing station name"
                )

            average_delay = parse_number(
                row[
                    headers["average_delay_min"]
                ],
                "average_delay"
            )

            right_time = parse_number(
                row[
                    headers[
                        "right_time_0_15_min_s"
                    ]
                ],
                "right_time"
            )

            slight_delay = parse_number(
                row[
                    headers[
                        "slight_delay_15_60_min_s"
                    ]
                ],
                "slight_delay"
            )

            significant_delay = parse_number(
                row[
                    headers[
                        "significant_delay_1_hour"
                    ]
                ],
                "significant_delay"
            )

            cancelled = parse_number(
                row[
                    headers["cancelled_unknown"]
                ],
                "cancelled_unknown"
            )

            # Average delay cannot be negative.

            if average_delay < 0:

                raise ValueError(
                    "average delay "
                    "cannot be negative"
                )

            percentages = [
                right_time,
                slight_delay,
                significant_delay,
                cancelled
            ]

            # Percentage values must be 0-100.

            for value in percentages:

                if value < 0 or value > 100:

                    raise ValueError(
                        "percentage value "
                        "outside 0-100 range"
                    )

            # The four categories should
            # approximately total 100%.

            percentage_total = sum(
                percentages
            )

            if not (
                99.0
                <= percentage_total
                <= 101.0
            ):

                warnings.append(
                    f"{path.name}, "
                    f"row {row_number}: "
                    f"percentage total is "
                    f"{percentage_total:.2f}, "
                    "expected ~100"
                )

            valid_rows += 1

        except ValueError as error:

            errors.append(
                f"{path.name}, "
                f"row {row_number}: "
                f"{error}"
            )

    return (
        errors,
        warnings,
        valid_rows
    )


def validate_routes(train_numbers):
    """Validate all route files."""

    print("\nROUTE FILE VALIDATION")
    print("-" * 55)

    errors = []
    warnings = []

    if not ROUTES_DIR.exists():

        errors.append(
            f"Missing route directory: "
            f"{ROUTES_DIR}"
        )

        return (
            errors,
            warnings,
            0,
            0
        )

    route_files = sorted(
        ROUTES_DIR.glob("*.csv")
    )

    print(
        f"Route files found       : "
        f"{len(route_files)}"
    )

    route_train_numbers = set()

    total_valid_rows = 0
    valid_files = 0

    for route_file in route_files:

        train_number = (
            route_file.stem.strip()
        )

        if not valid_train_number(
            train_number
        ):

            errors.append(
                f"{route_file.name}: "
                "invalid filename "
                "(expected train number)"
            )

            continue

        route_train_numbers.add(
            train_number
        )

        if train_number not in train_numbers:

            errors.append(
                f"{route_file.name}: "
                "train not present in "
                "Train_List.csv"
            )

        (
            file_errors,
            file_warnings,
            valid_rows
        ) = validate_route_file(
            route_file
        )

        errors.extend(
            file_errors
        )

        warnings.extend(
            file_warnings
        )

        if not file_errors:

            valid_files += 1

        total_valid_rows += (
            valid_rows
        )

    # Find trains without route files.

    missing_routes = (
        train_numbers
        - route_train_numbers
    )

    for train_number in sorted(
        missing_routes
    ):

        errors.append(
            f"Missing route file "
            f"for train {train_number}"
        )

    print(
        f"Valid route files       : "
        f"{valid_files}"
    )

    print(
        f"Valid route records     : "
        f"{total_valid_rows}"
    )

    print(
        f"Missing route files     : "
        f"{len(missing_routes)}"
    )

    return (
        errors,
        warnings,
        valid_files,
        total_valid_rows
    )


# =========================================================
# MAIN VALIDATION
# =========================================================

def main():
    """Run complete dataset validation."""

    print("=" * 55)

    print(
        "             DATA VALIDATION"
    )

    print("=" * 55)

    (
        train_errors,
        train_warnings,
        train_numbers
    ) = validate_train_list()

    (
        route_errors,
        route_warnings,
        valid_files,
        valid_rows
    ) = validate_routes(
        train_numbers
    )

    errors = (
        train_errors
        + route_errors
    )

    warnings = (
        train_warnings
        + route_warnings
    )

    print("\nVALIDATION SUMMARY")
    print("-" * 55)

    print(
        f"Errors                  : "
        f"{len(errors)}"
    )

    print(
        f"Warnings                : "
        f"{len(warnings)}"
    )

    if errors:

        print("\nERRORS")
        print("-" * 55)

        for error in errors:

            print(
                f"X {error}"
            )

    if warnings:

        print("\nWARNINGS")
        print("-" * 55)

        for warning in warnings:

            print(
                f"! {warning}"
            )

    print("\n" + "=" * 55)

    if errors:

        print(
            "STATUS                  : INVALID"
        )

        print("=" * 55)

        return 1

    print(
        "STATUS                  : VALID"
    )

    print("=" * 55)

    return 0


if __name__ == "__main__":

    sys.exit(
        main()
    )
