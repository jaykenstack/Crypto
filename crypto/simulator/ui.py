# simulator/ui.py
"""
User interface components for the scanner
"""

import time
import sys
from typing import Optional


def display_error(error_message: str):
    """Display an error message"""
    print(f"\n❌ ERROR: {error_message}")


class ConsoleUI:
    """Console-based user interface for the scanner"""

    def __init__(self, stats, refresh_interval: float = 0.5):
        self.stats = stats
        self.refresh_interval = refresh_interval
        self.last_update = 0
        self.start_time = time.time()
        self.lines_printed = 0

    @staticmethod
    def clear_lines(num_lines: int):
        """Clear specified number of lines in console"""
        for _ in range(num_lines):
            sys.stdout.write('\033[F')  # Move cursor up one line
            sys.stdout.write('\033[K')  # Clear line

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds into HH:MM:SS or MM:SS"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.0f}s"

    @staticmethod
    def format_large_number(num: float) -> str:
        """Format large numbers with K, M, B suffixes"""
        if num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return f"{num:,.0f}"

    @staticmethod
    def create_progress_bar(progress: float, width: int = 40) -> str:
        """Create a text-based progress bar"""
        filled_width = int(width * progress / 100)
        bar = '█' * filled_width + '░' * (width - filled_width)
        return f"[{bar}] {progress:.1f}%"

    # In simulator/ui.py, update the display_summary method:
    def display_summary(self):
        """Display final summary of the scan with seed phrases"""

        print("\n" + "═" * 70)
        print("💰 WALLET SCAN COMPLETE - FINAL REPORT")
        print("═" * 70)

        # ... [previous summary code remains]

        # Display active wallets with seed phrases
        active_wallets = [r for r in self.stats.results if r.is_active]
        if active_wallets:
            # Get unique wallets
            unique_wallets = {}
            for wallet in active_wallets:
                if wallet.address not in unique_wallets:
                    unique_wallets[wallet.address] = wallet

            # Sort by balance
            sorted_wallets = sorted(
                unique_wallets.values(),
                key=lambda x: x.balance,
                reverse=True
            )

            print(f"\n🔐 ACTIVE WALLETS FOUND (with Seed Phrases)")
            print("═" * 70)

            for i, wallet in enumerate(sorted_wallets[:10], 1):
                print(f"\n🏆 WALLET #{i}")
                print("-" * 40)
                print(f"Type:        {wallet.address_type.upper()}")
                print(f"Balance:     {wallet.balance:.8f}")
                print(f"Transactions: {wallet.transaction_count:,}")
                print(f"Address:     {wallet.address[:30]}...")
                print(f"\n📝 24-WORD SEED PHRASE:")
                print("-" * 40)

                # Display seed phrase in formatted columns
                if hasattr(wallet, 'seed_phrase') and wallet.seed_phrase:
                    words = wallet.seed_phrase.split()
                    for row in range(0, 24, 6):
                        line = []
                        for col in range(6):
                            idx = row + col
                            if idx < 24:
                                line.append(f"{idx + 1:2}. {words[idx]:<10}")
                        print("  ".join(line))
                else:
                    print("  (Seed phrase not available)")

                if hasattr(wallet, 'tags') and wallet.tags:
                    print(f"Tags:        {', '.join(wallet.tags)}")

                print("-" * 40)

        print("\n" + "═" * 70)
        # Display top wallets if any
        active_wallets = [r for r in self.stats.results if r.is_active]
        if active_wallets:
            # Sort by balance descending
            active_wallets.sort(key=lambda x: x.balance, reverse=True)

            print(f"\n🏆 TOP 10 WALLETS BY BALANCE")
            print("─" * 40)
            for i, wallet in enumerate(active_wallets[:10], 1):
                balance_str = f"{wallet.balance:12.8f}"
                print(f"   {i:2}. {wallet.address[:20]}... | "
                      f"Balance: {balance_str} | "
                      f"TXs: {wallet.transaction_count:5,} | "
                      f"Type: {wallet.address_type.upper()}")

        print("\n" + "═" * 70)

    def update_display(self, force: bool = False):
        """Update the console display with current statistics"""
        current_time = time.time()

        # Only update at specified interval
        if not force and current_time - self.last_update < self.refresh_interval:
            return

        self.last_update = current_time
        summary = self.stats.get_summary()

        # Clear previous output
        if self.lines_printed > 0:
            self.clear_lines(self.lines_printed)

        # Prepare display lines
        lines = []

        # Header
        elapsed = self.format_time(summary['elapsed_time'])
        lines.append(f"⏱️  Elapsed: {elapsed} | "
                     f"📡 Status: {summary['status'].upper()} | "
                     f"⚡ Speed: {summary['scan_rate']:.1f}/sec")
        lines.append("")

        # Progress
        progress_bar = self.create_progress_bar(summary['progress'])
        lines.append(f"📊 Progress: {progress_bar}")
        lines.append(f"   Scanned: {summary['scanned_addresses']:,} / {summary['total_addresses']:,}")
        lines.append("")

        # Statistics
        lines.append(f"✅ Success Rate: {summary['success_rate']:.2f}% | "
                     f"✅ Successful: {summary['successful_scans']:,} | "
                     f"❌ Failed: {summary['failed_scans']:,}")
        lines.append("")

        # Discoveries
        lines.append(f"💰 Active Wallets: {summary['active_wallets']:,} | "
                     f"🏦 Rich Wallets: {summary['rich_wallets']:,}")
        lines.append(f"💎 Total Balance: {summary['total_balance']:.8f} | "
                     f"📈 Average: {summary['average_balance']:.8f}")

        # Per-type statistics (if available)
        if 'type_stats' in summary and summary['type_stats']:
            lines.append("")
            lines.append("🔢 By Type: ")
            type_lines = []
            for addr_type, stats in summary['type_stats'].items():
                if stats['count'] > 0:
                    type_lines.append(f"{addr_type[:3].upper()}:{stats['count']:,}")
            lines[-1] += " | ".join(type_lines)

        # Print all lines
        for line in lines:
            print(line)

        # Store how many lines we printed
        self.lines_printed = len(lines)

    @staticmethod
    def display_warning(warning_message: str):
        """Display a warning message"""
        print(f"\n⚠️  WARNING: {warning_message}")

    @staticmethod
    def display_info(info_message: str):
        """Display an information message"""
        print(f"\nℹ️  INFO: {info_message}")