#!/usr/bin/env python3
"""
Wallet Scanner Simulator - Main Entry Point
"""

import sys
import os
import time
import signal
import threading
from typing import Optional

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Debug info
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {current_dir}")

# Import settings
try:
    from config.settings import settings

    print("✓ Successfully imported settings")
except ImportError:
    print("Note: Using default settings...")


    # Create default settings
    class DefaultSettings:
        NUM_ADDRESSES = 1000
        MAX_WORKERS = 4
        BATCH_SIZE = 50
        SCAN_DELAY = 0.01
        SIMULATION_SPEED = 100
        ACTIVE_PROBABILITY = 0.05
        RICH_PROBABILITY = 0.01


    settings = DefaultSettings()

# Import simulator modules - use importlib to avoid circular imports
simulator_dir = os.path.join(current_dir, 'simulator')
print(f"\nSimulator directory: {simulator_dir}")
print("Files in simulator directory:")
for f in os.listdir(simulator_dir):
    print(f"  - {f}")

print("\nImporting simulator modules...")

# Import each module directly using importlib
import importlib.util

try:
    # Import generator
    generator_spec = importlib.util.spec_from_file_location(
        "generator",
        os.path.join(simulator_dir, 'generator.py')
    )
    generator_module = importlib.util.module_from_spec(generator_spec)
    generator_spec.loader.exec_module(generator_module)
    AddressGenerator = generator_module.AddressGenerator
    WalletAddress = generator_module.WalletAddress
    print("✓ Imported generator module")

    # Import stats
    stats_spec = importlib.util.spec_from_file_location(
        "stats",
        os.path.join(simulator_dir, 'stats.py')
    )
    stats_module = importlib.util.module_from_spec(stats_spec)
    stats_spec.loader.exec_module(stats_module)
    Statistics = stats_module.Statistics
    ScanStatus = stats_module.ScanStatus
    ScanResult = stats_module.ScanResult  # Get ScanResult from stats module
    print("✓ Imported stats module")

    # Import worker - inject ScanResult to avoid circular import
    worker_spec = importlib.util.spec_from_file_location(
        "worker",
        os.path.join(simulator_dir, 'worker.py')
    )
    worker_module = importlib.util.module_from_spec(worker_spec)
    # Inject ScanResult into worker module
    worker_module.ScanResult = ScanResult
    worker_spec.loader.exec_module(worker_module)
    Scanner = worker_module.Scanner
    print("✓ Imported worker module")

    # Import ui
    ui_spec = importlib.util.spec_from_file_location(
        "ui",
        os.path.join(simulator_dir, 'ui.py')
    )
    ui_module = importlib.util.module_from_spec(ui_spec)
    ui_spec.loader.exec_module(ui_module)
    ConsoleUI = ui_module.ConsoleUI
    print("✓ Imported ui module")

    print("\n✅ All modules imported successfully!")

except Exception as e:
    print(f"\n❌ Error importing modules: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)


class WalletScannerSimulator:
    """Main application class for the wallet scanner simulator"""

    def __init__(self):
        """Initialize the simulator with all components"""
        self.generator = AddressGenerator()
        self.stats = Statistics()
        self.scanner = Scanner(self.stats)
        self.ui = ConsoleUI(self.stats)
        self.running = False
        self.paused = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum):
        """Handle interrupt signals (Ctrl+C) gracefully"""
        print(f"\n\nReceived signal {signum}, handling shutdown...")

        if self.running and not self.paused:
            print("Scan paused. Press Ctrl+C again to quit.")
            self.paused = True
            self.scanner.stop()
        else:
            print("Exiting simulator...")
            self.cleanup()
            sys.exit(0)

    def generate_addresses(self) -> list:
        """Generate mock wallet addresses for scanning"""
        print("\n" + "=" * 60)
        print("WALLET ADDRESS GENERATION")
        print("=" * 60)

        total_addresses = settings.NUM_ADDRESSES
        print(f"\nGenerating {total_addresses:,} mock wallet addresses...")

        addresses = self.generator.generate_all()

        # Count addresses by type
        type_counts = {}
        for addr in addresses:
            addr_type = addr.address_type.value
            type_counts[addr_type] = type_counts.get(addr_type, 0) + 1

        print(f"\n✓ Generated {len(addresses):,} wallet addresses:")
        for addr_type, count in sorted(type_counts.items()):
            print(f"  • {addr_type.upper()}: {count:,}")

        # Calculate expected active wallets based on probabilities
        estimated_active = int(len(addresses) * settings.ACTIVE_PROBABILITY)
        estimated_rich = int(len(addresses) * settings.RICH_PROBABILITY)

        print(f"\nExpected findings (based on probabilities):")
        print(f"  • Active wallets: {estimated_active:,}")
        print(f"  • Rich wallets (>1000): {estimated_rich:,}")

        return addresses

    def run_scan(self, addresses: list):
        """Run the wallet scanning process"""
        print("\n" + "=" * 60)
        print("STARTING WALLET SCAN")
        print("=" * 60)

        print(f"\nConfiguration:")
        print(f"  • Worker threads: {min(settings.MAX_WORKERS, len(addresses))}")
        print(f"  • Batch size: {settings.BATCH_SIZE}")
        print(f"  • Scan delay: {settings.SCAN_DELAY}s per address")
        print(f"  • Simulation speed: {settings.SIMULATION_SPEED}x")

        print("\n" + "-" * 40)
        print("Press Ctrl+C to pause the scan")
        print("Press Ctrl+C again to quit")
        print("-" * 40 + "\n")

        # Brief pause before starting
        time.sleep(2)

        # Initialize statistics
        self.stats.start_scan(len(addresses))
        self.running = True

        # Create a thread for the scan
        scan_thread = threading.Thread(
            target=self._run_scan_thread,
            args=(addresses,),
            daemon=True
        )
        scan_thread.start()

        # Update UI while scanning
        try:
            while scan_thread.is_alive() and self.running:
                if not self.paused:
                    self.ui.update_display()
                time.sleep(0.1)

            # Wait for scan to complete
            scan_thread.join(timeout=5)

        except KeyboardInterrupt:
            print("\nScan interrupted by user")
            self.scanner.stop()

        # Final UI update
        if not self.paused:
            self.ui.update_display()

        # Display final summary
        if self.stats.status == ScanStatus.COMPLETED:
            time.sleep(1)  # Brief pause before summary
            print("\n" + "=" * 60)
            print("SCAN COMPLETE - GENERATING REPORT")
            print("=" * 60)
            self.ui.display_summary()

        self.running = False

    def _run_scan_thread(self, addresses: list):
        """Run the actual scan in a separate thread"""
        try:
            print("Starting scan workers...")
            results = self.scanner.scan(addresses)
            self.stats.complete_scan()
            print(f"\n✓ Scan completed. Processed {len(results):,} addresses.")

        except Exception as scan_err:
            print(f"\n✗ Error during scan: {scan_err}")
            import traceback
            traceback.print_exc()
            self.stats.status = ScanStatus.ERROR

    # In main.py, update the save_results method:
    def save_results(self):
        """Save scan results to a file including seed phrases"""
        if not self.stats.results:
            print("\nNo results to save.")
            return

        print("\n" + "=" * 60)
        response = input("Would you like to save the scan results to a file? (y/N): ")

        if response.lower() == 'y':
            default_name = f"wallet_scan_{int(time.time())}.txt"
            filename = input(f"Enter filename (default: {default_name}): ") or default_name

            try:
                with open(filename, 'w') as f:
                    f.write("=" * 70 + "\n")
                    f.write("WALLET SCANNER SIMULATOR - RESULTS WITH SEED PHRASES\n")
                    f.write("=" * 70 + "\n\n")

                    # ... [previous summary writing code remains]

                    # Write active wallets with seed phrases
                    if self.stats.active_wallets > 0:
                        f.write("ACTIVE WALLETS FOUND (WITH SEED PHRASES)\n")
                        f.write("=" * 70 + "\n\n")

                        # Get unique wallets
                        unique_wallets = {}
                        for result in self.stats.results:
                            if result.is_active and result.address not in unique_wallets:
                                unique_wallets[result.address] = result

                        active_wallets = sorted(
                            unique_wallets.values(),
                            key=lambda x: x.balance,
                            reverse=True
                        )

                        for i, result in enumerate(active_wallets, 1):
                            f.write(f"WALLET #{i}\n")
                            f.write("-" * 40 + "\n")
                            f.write(f"Type:        {result.address_type.upper()}\n")
                            f.write(f"Address:     {result.address}\n")
                            f.write(f"Balance:     {result.balance:.8f}\n")
                            f.write(f"Transactions: {result.transaction_count:,}\n")
                            f.write(f"Status:      {'Active' if result.is_active else 'Inactive'}\n")

                            # Write seed phrase
                            if hasattr(result, 'seed_phrase') and result.seed_phrase:
                                f.write(f"\n24-WORD SEED PHRASE:\n")
                                f.write("-" * 40 + "\n")
                                words = result.seed_phrase.split()
                                for row in range(0, 24, 6):
                                    line = []
                                    for col in range(6):
                                        idx = row + col
                                        if idx < 24:
                                            line.append(f"{idx + 1:2}. {words[idx]}")
                                    f.write("  ".join(line) + "\n")
                                f.write("-" * 40 + "\n")
                            else:
                                f.write("Seed Phrase: (not available)\n")

                            if result.tags:
                                f.write(f"Tags:        {', '.join(result.tags)}\n")

                            f.write("\n" + "=" * 70 + "\n\n")

                    # ... [rest of configuration writing code remains]

                print(f"\n✓ Results saved to '{filename}'")

            except Exception as save_err:
                print(f"\n✗ Error saving results: {save_err}")
                import traceback
                traceback.print_exc()
        else:
            print("\nResults not saved.")

    def cleanup(self):
        """Clean up resources"""
        print("\nCleaning up resources...")
        self.scanner.stop()
        self.running = False
        print("Cleanup complete.")

    def run(self):
        """Main application loop"""
        print("\n" + "=" * 60)
        print("WALLET SCANNER SIMULATOR")
        print("=" * 60)
        print("Version 1.0.0")
        print("A demonstration of wallet scanning concepts\n")

        try:
            # Step 1: Generate addresses
            addresses = self.generate_addresses()

            # Step 2: Run the scan
            self.run_scan(addresses)

            # Step 3: Save results if desired
            self.save_results()

        except KeyboardInterrupt:
            print("\n\nSimulator interrupted by user.")
        except Exception as run_err:
            print(f"\n\nUnexpected error: {run_err}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("\n" + "=" * 60)
        print("Thank you for using Wallet Scanner Simulator!")
        print("=" * 60 + "\n")


def main():
    """Main entry point function"""
    print("Initializing Wallet Scanner Simulator...")

    # Display configuration
    print(f"\nCurrent Configuration:")
    print(f"  • Addresses to generate: {settings.NUM_ADDRESSES:,}")
    print(f"  • Worker threads: {settings.MAX_WORKERS}")
    print(f"  • Active wallet probability: {settings.ACTIVE_PROBABILITY:.6f}")
    print(f"  • Rich wallet probability: {settings.RICH_PROBABILITY:.6f}")
    print(f"  • Simulation speed: {settings.SIMULATION_SPEED}x")

    # Ask if user wants to modify settings
    modify = input("\nModify settings before starting? (y/N): ")
    if modify.lower() == 'y':
        try:
            num = input(f"Number of addresses [{settings.NUM_ADDRESSES}]: ")
            if num:
                settings.NUM_ADDRESSES = int(num)

            workers = input(f"Worker threads [{settings.MAX_WORKERS}]: ")
            if workers:
                settings.MAX_WORKERS = int(workers)

            print(f"\nUpdated Configuration:")
            print(f"  • Addresses to generate: {settings.NUM_ADDRESSES:,}")
            print(f"  • Worker threads: {settings.MAX_WORKERS}")
        except ValueError:
            print("Invalid input, using default settings.")

    # Create and run the simulator
    simulator = WalletScannerSimulator()
    simulator.run()


if __name__ == "__main__":
    main()