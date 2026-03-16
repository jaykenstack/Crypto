# simulator/stats.py
"""
Statistics and metrics tracking for the scanner
"""

import time
from typing import List, Dict, Any, Optional  # ADD Optional here!
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict


class ScanStatus(Enum):
    """Status of the scan process"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ScanResult:
    """Result of scanning a single wallet address"""
    address: str
    address_type: str
    seed_phrase: str  # Added seed phrase field
    balance: float
    transaction_count: int
    is_active: bool
    tags: List[str]
    scan_time: float
    success: bool
    error: Optional[str] = None  # Now Optional is defined


# ... rest of your stats.py code remains the same ...


class Statistics:
    """Tracks and manages scan statistics"""

    def __init__(self):
        self.type_stats = None
        self.start_time = None
        self.failed_scans = None
        self.end_time = None
        self.scanned_addresses = None
        self.successful_scans = None
        self.active_wallets = None
        self.rich_wallets = None
        self.total_balance = None
        self.results = None
        self.status = None
        self.total_addresses = None
        self.reset()

    def reset(self):
        """Reset all statistics"""
        self.start_time = None
        self.end_time = None
        self.total_addresses = 0
        self.scanned_addresses = 0
        self.successful_scans = 0
        self.failed_scans = 0
        self.active_wallets = 0
        self.total_balance = 0.0
        self.rich_wallets = 0  # Wallets with balance > 1000
        self.results = []
        self.status = ScanStatus.IDLE

        # Per-type statistics
        self.type_stats = defaultdict(lambda: {
            'count': 0,
            'active': 0,
            'balance': 0.0,
            'rich': 0
        })

    def start_scan(self, total_addresses: int):
        """Start tracking a new scan"""
        self.reset()
        self.start_time = time.time()
        self.total_addresses = total_addresses
        self.status = ScanStatus.RUNNING
        print(f"Scan started for {total_addresses} addresses at {time.ctime(self.start_time)}")

    def increment_scanned(self):
        """Increment scanned address counter"""
        self.scanned_addresses += 1

    def add_successful_scan(self):
        """Increment successful scan counter"""
        self.successful_scans += 1

    def add_failed_scan(self):
        """Increment failed scan counter"""
        self.failed_scans += 1

    def add_active_wallet(self, result: ScanResult):
        """Add an active wallet to statistics"""
        self.active_wallets += 1
        self.total_balance += result.balance

        # Check if rich wallet
        if result.balance > 1000:
            self.rich_wallets += 1

        # Update type statistics
        addr_type = result.address_type
        self.type_stats[addr_type]['count'] += 1
        self.type_stats[addr_type]['balance'] += result.balance

        if result.is_active:
            self.type_stats[addr_type]['active'] += 1

        if result.balance > 1000:
            self.type_stats[addr_type]['rich'] += 1

        # Store result
        self.results.append(result)

    def add_result(self, result: ScanResult):
        """Add a scan result to statistics"""
        self.scanned_addresses += 1

        if result.success:
            self.successful_scans += 1
            if result.is_active:
                self.add_active_wallet(result)
        else:
            self.failed_scans += 1

        self.results.append(result)

    def complete_scan(self):
        """Mark scan as completed"""
        self.end_time = time.time()
        self.status = ScanStatus.COMPLETED
        print(f"Scan completed at {time.ctime(self.end_time)}")

    def pause_scan(self):
        """Pause the scan"""
        self.status = ScanStatus.PAUSED

    def resume_scan(self):
        """Resume the scan"""
        self.status = ScanStatus.RUNNING

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        elif self.end_time is None:
            return time.time() - self.start_time
        else:
            return self.end_time - self.start_time

    def get_progress(self) -> float:
        """Get scan progress as percentage"""
        if self.total_addresses == 0:
            return 0.0
        return (self.scanned_addresses / self.total_addresses) * 100

    def get_scan_rate(self) -> float:
        """Get scan rate in addresses per second"""
        elapsed = self.get_elapsed_time()
        if elapsed == 0:
            return 0.0
        return self.scanned_addresses / elapsed

    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.scanned_addresses == 0:
            return 0.0
        return (self.successful_scans / self.scanned_addresses) * 100

    def get_average_balance(self) -> float:
        """Get average balance of active wallets"""
        if self.active_wallets == 0:
            return 0.0
        return self.total_balance / self.active_wallets

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all statistics"""
        return {
            'status': self.status.value,
            'total_addresses': self.total_addresses,
            'scanned_addresses': self.scanned_addresses,
            'progress': self.get_progress(),
            'successful_scans': self.successful_scans,
            'failed_scans': self.failed_scans,
            'success_rate': self.get_success_rate(),
            'active_wallets': self.active_wallets,
            'rich_wallets': self.rich_wallets,
            'total_balance': self.total_balance,
            'average_balance': self.get_average_balance(),
            'elapsed_time': self.get_elapsed_time(),
            'scan_rate': self.get_scan_rate(),
            'type_stats': dict(self.type_stats)
        }

    def print_summary(self):
        """Print a formatted summary of statistics"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("SCAN SUMMARY")
        print("="*60)

        print(f"\nStatus: {summary['status'].upper()}")
        print(f"Progress: {summary['progress']:.1f}% ({summary['scanned_addresses']}/{summary['total_addresses']})")
        print(f"Elapsed Time: {summary['elapsed_time']:.2f} seconds")
        print(f"Scan Rate: {summary['scan_rate']:.1f} addresses/second")

        print(f"\nSuccess Rate: {summary['success_rate']:.2f}%")
        print(f"Successful Scans: {summary['successful_scans']:,}")
        print(f"Failed Scans: {summary['failed_scans']:,}")

        print(f"\nActive Wallets Found: {summary['active_wallets']:,}")
        print(f"Rich Wallets (>1000): {summary['rich_wallets']:,}")
        print(f"Total Balance: {summary['total_balance']:.8f}")
        print(f"Average Balance: {summary['average_balance']:.8f}")

        # Print per-type statistics
        if self.type_stats:
            print(f"\nBreakdown by Address Type:")
            print("-"*40)
            for addr_type, stats in self.type_stats.items():
                if stats['count'] > 0:
                    print(f"{addr_type.upper()}:")
                    print(f"  Count: {stats['count']:,}")
                    print(f"  Active: {stats['active']:,}")
                    print(f"  Rich: {stats['rich']:,}")
                    print(f"  Total Balance: {stats['balance']:.8f}")