import os
from collections import defaultdict

LOG_FILES = {
    "debug": "logs/debug.log",
    "db": "logs/db.log",
    "api": "logs/api.log",
    "integrations": "logs/integrations.log",
    "models": "logs/models.log",
    "services": "logs/services.log",
    "errors": "logs/errors.log",
}


def _analyze_log_file(path: str):
    """
    Returns summary stats for a single log file:
    - line count
    - counts per log level (INFO, DEBUG, WARNING, ERROR, etc.)
    """
    stats = {
        "lines": 0,
        "levels": defaultdict(int),
        "missing": False,
    }

    if not os.path.exists(path):
        stats["missing"] = True
        return stats

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stats["lines"] += 1

            # Your format: "... | LEVEL | ..."
            # Example: 2025-01-01 12:00:00 | ERROR    | src.api | message
            parts = line.split("|")
            if len(parts) >= 2:
                level = parts[1].strip()
                stats["levels"][level] += 1

    return stats


def print_log_summary():
    """
    Prints a human-readable summary of all log files.
    """
    print("\n=== LOG SUMMARY ===\n")

    grand_total_lines = 0
    total_levels = defaultdict(int)

    for name, path in LOG_FILES.items():
        stats = _analyze_log_file(path)

        print(f"[{name}]")
        if stats["missing"]:
            print("  ❌ File not found")
            continue

        print(f"  Total lines: {stats['lines']}")
        grand_total_lines += stats["lines"]

        if stats["levels"]:
            for level, count in sorted(stats["levels"].items()):
                print(f"  {level:<8}: {count}")
                total_levels[level] += count
        else:
            print("  No parsed log levels found")

        print()

    print("=== AGGREGATE ===")
    print(f"Total lines across all logs: {grand_total_lines}")

    if total_levels:
        print("Total by level:")
        for level, count in sorted(total_levels.items()):
            print(f"  {level:<8}: {count}")

    print("\n===================\n")
    
if __name__ == "__main__":
    print_log_summary()