# simulator/worker.py
"""
Worker module for scanning wallet addresses
"""

import time
import random
import threading
from typing import List, Optional
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum


class ScanStatus(Enum):
    """Status of scan operation"""
    PENDING = "pending"
    SCANNING = "scanning"
    COMPLETED = "completed"
    ERROR = "error"


# Define a LOCAL ScanResult class to avoid import issues
@dataclass
class WorkerScanResult:
    """Result of scanning a single wallet address (for worker module)"""
    address: str
    address_type: str
    balance: float
    transaction_count: int
    is_active: bool
    tags: List[str]
    scan_time: float
    success: bool
    error: Optional[str] = None


# noinspection PyArgumentList
class Worker(threading.Thread):
    """Individual worker thread for scanning addresses"""

    def __init__(self, worker_id: int, task_queue: Queue, result_queue: Queue,
                 stats, delay: float = 0.01):
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.stats = stats
        self.delay = delay
        self.running = True

    def run(self):
        """Main worker loop"""
        print(f"Worker {self.worker_id} started")
        while self.running:
            try:
                # Get task from queue
                wallet = self.task_queue.get(timeout=1.0)  # Increased timeout

                if wallet is None:  # Sentinel value to stop
                    self.task_queue.task_done()
                    break

                # Scan the wallet
                result = self._scan_wallet(wallet)

                # Put result in result queue
                self.result_queue.put(result)

                # Update statistics through stats object
                if hasattr(self.stats, 'add_result'):
                    self.stats.add_result(result)

                # Simulate network delay
                time.sleep(self.scan_delay)

                # Mark task as done
                self.task_queue.task_done()

            except Empty:
                # No tasks available, check if we should continue
                if not self.running or self.task_queue.empty():
                    continue
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
                self.task_queue.task_done()

        print(f"Worker {self.worker_id} stopped")

    def scan(self, addresses: List) -> List[ScanResult]:
        """Scan a list of wallet addresses"""
        print(f"Starting scan of {len(addresses)} addresses with {self.max_workers} workers...")

        self.running = True
        results = []

        # Create and start workers FIRST
        self._create_workers()

        # Add ALL addresses to task queue BEFORE processing
        print(f"Adding {len(addresses)} addresses to queue...")
        for wallet in addresses:
            self.task_queue.put(wallet)

        print(f"Queue filled with {self.task_queue.qsize()} addresses")

        # Wait for all tasks to complete
        print("Waiting for tasks to complete...")
        self.task_queue.join()  # This blocks until all tasks are done

        # Get all results from result queue
        print("Collecting results...")
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
            except Empty:
                break

        # Stop all workers
        self.stop()

        print(f"\n✓ Scan completed. Total results: {len(results)}")
        return results

    def stop(self):
        """Stop the worker"""
        self.running = False


class Scanner:
    """Main scanner class that manages workers and scanning process"""

    def __init__(self, stats, max_workers: int = 4, batch_size: int = 50,
                 scan_delay: float = 0.01):
        self.stats = stats
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.scan_delay = scan_delay
        self.workers = []
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.running = False

    def scan(self, addresses: List) -> List[WorkerScanResult]:
        """Scan a list of wallet addresses"""
        print(f"Starting scan of {len(addresses)} addresses with {self.max_workers} workers...")

        self.running = True
        results = []

        # Create and start workers
        self._create_workers()

        # Add addresses to task queue in batches
        total_batches = (len(addresses) + self.batch_size - 1) // self.batch_size

        for batch_num in range(total_batches):
            if not self.running:
                break

            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(addresses))
            batch = addresses[start_idx:end_idx]

            # Add batch to queue
            for wallet in batch:
                self.task_queue.put(wallet)

            if batch_num % 100 == 0:  # Print progress every 100 batches
                print(f"  Batch {batch_num + 1}/{total_batches} queued ({len(batch)} addresses)")

            # Process some results while queuing next batch
            self._process_results(results, len(batch))

        # Wait for all tasks to complete
        self.task_queue.join()

        # Get any remaining results
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                results.append(result)
            except Empty:
                break

        # Stop all workers
        self.stop()

        print(f"\n✓ Scan completed. Total results: {len(results)}")
        return results

    def _create_workers(self):
        """Create and start worker threads"""
        self.workers = []
        for i in range(self.max_workers):
            worker = Worker(
                worker_id=i + 1,
                task_queue=self.task_queue,
                result_queue=self.result_queue,
                stats=self.stats,
                delay=self.scan_delay
            )
            self.workers.append(worker)

        print(f"Starting {len(self.workers)} worker threads...")
        for worker in self.workers:
            worker.start()

        print(f"Started {len(self.workers)} worker threads")

    def _process_results(self, results: List, expected_count: int):
        """Process available results from queue"""
        processed = 0
        while processed < expected_count and not self.result_queue.empty():
            try:
                result = self.result_queue.get(timeout=0.1)
                results.append(result)
                processed += 1
            except Empty:
                break

    def stop(self):
        """Stop the scanner and all workers"""
        self.running = False

        # Stop all workers
        for worker in self.workers:
            worker.stop()

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=1)

        print("Scanner stopped")