import csv
from datetime import datetime, UTC
from pathlib import Path

from .models import Account, AccountStatusInfo, Transaction


class LegacyDataAdapter:
    """Adapter over nightly CSV exports from a legacy core banking platform."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.accounts_file = self.data_dir / "legacy_accounts.csv"
        self.transactions_file = self.data_dir / "legacy_transactions.csv"
        self.account_status_info_file = self.data_dir / "legacy_account_status_info.csv"

    def load_accounts(self) -> list[Account]:
        accounts: list[Account] = []
        with self.accounts_file.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                accounts.append(Account(**row))
        return accounts

    def load_transactions(self) -> list[Transaction]:
        transactions: list[Transaction] = []
        with self.transactions_file.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                transactions.append(Transaction(**row))
        return transactions

    def latest_transaction_activity(self, account_id: str) -> datetime | None:
        transactions = self.load_transactions()
        matching = [tx.posted_at for tx in transactions if tx.account_id == account_id]
        if not matching:
            return None
        return max(matching)

    def load_account_status_info(self) -> list[AccountStatusInfo]:
        status_items: list[AccountStatusInfo] = []
        with self.account_status_info_file.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                normalized_row = {key: (value if value != "" else None) for key, value in row.items()}
                status_items.append(AccountStatusInfo(**normalized_row))
        return status_items

    def latest_refresh_timestamp(self) -> datetime:
        accounts_mtime = datetime.fromtimestamp(self.accounts_file.stat().st_mtime, tz=UTC)
        tx_mtime = datetime.fromtimestamp(self.transactions_file.stat().st_mtime, tz=UTC)
        return max(accounts_mtime, tx_mtime)
