import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.security import list_users, set_user_active, upsert_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage demo users for legacy-bank-api")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List users")
    list_parser.set_defaults(command="list")

    add_parser = subparsers.add_parser("add", help="Add or update a user")
    add_parser.add_argument("--username", required=True)
    add_parser.add_argument("--password", required=True)
    add_parser.add_argument("--role", default="viewer", choices=["admin", "viewer"])
    add_parser.add_argument("--inactive", action="store_true", help="Create/update as inactive")

    activate_parser = subparsers.add_parser("activate", help="Activate a user")
    activate_parser.add_argument("--username", required=True)

    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate a user")
    deactivate_parser.add_argument("--username", required=True)

    args = parser.parse_args()

    if args.command == "list":
        for user in list_users():
            print(f"{user['username']} | role={user['role']} | active={user['active']}")
        return

    if args.command == "add":
        upsert_user(
            username=args.username,
            password=args.password,
            role=args.role,
            active=not args.inactive,
        )
        print(f"User '{args.username}' upserted.")
        return

    if args.command == "activate":
        if set_user_active(args.username, True):
            print(f"User '{args.username}' activated.")
        else:
            print(f"User '{args.username}' not found.")
        return

    if args.command == "deactivate":
        if set_user_active(args.username, False):
            print(f"User '{args.username}' deactivated.")
        else:
            print(f"User '{args.username}' not found.")


if __name__ == "__main__":
    main()
