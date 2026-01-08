"""
Performance baseline testing script for Transfer2Read.

This script executes performance baseline tests without requiring full system integration.
Tests focus on API responsiveness, Docker resource usage, and system health under load.
"""

import time
import statistics
import subprocess
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

import requests


class PerformanceBaseline:
    """Performance baseline testing for API endpoints and system resources."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }

    def test_health_endpoint_performance(self, num_requests: int = 100) -> Dict[str, Any]:
        """
        Test /api/health endpoint performance.

        Args:
            num_requests: Number of requests to make

        Returns:
            Dictionary with performance metrics
        """
        print(f"\n📊 Testing /api/health endpoint ({num_requests} requests)...")

        response_times = []
        failures = 0

        for i in range(num_requests):
            start = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=5)
                elapsed = (time.time() - start) * 1000  # milliseconds

                if response.status_code == 200:
                    response_times.append(elapsed)
                else:
                    failures += 1
            except Exception as e:
                failures += 1
                print(f"Request {i+1} failed: {e}")

            # Small delay to avoid overwhelming the server
            time.sleep(0.01)

        if response_times:
            metrics = {
                "test": "health_endpoint",
                "total_requests": num_requests,
                "successful_requests": len(response_times),
                "failed_requests": failures,
                "avg_response_time_ms": statistics.mean(response_times),
                "median_response_time_ms": statistics.median(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "p95_response_time_ms": self._percentile(response_times, 95),
                "p99_response_time_ms": self._percentile(response_times, 99),
                "target_p95_ms": 500,
                "target_p99_ms": 1000,
                "p95_pass": self._percentile(response_times, 95) < 500,
                "p99_pass": self._percentile(response_times, 99) < 1000
            }

            print(f"✓ Avg: {metrics['avg_response_time_ms']:.2f}ms")
            print(f"✓ P95: {metrics['p95_response_time_ms']:.2f}ms (target: <500ms) - {'PASS' if metrics['p95_pass'] else 'FAIL'}")
            print(f"✓ P99: {metrics['p99_response_time_ms']:.2f}ms (target: <1000ms) - {'PASS' if metrics['p99_pass'] else 'FAIL'}")

            self.results["tests"].append(metrics)
            return metrics
        else:
            print("❌ All requests failed")
            return {"test": "health_endpoint", "error": "all_requests_failed"}

    def test_docker_resource_usage(self) -> Dict[str, Any]:
        """
        Test Docker container resource usage using docker stats.

        Returns:
            Dictionary with resource usage metrics
        """
        print("\n📊 Collecting Docker resource usage...")

        try:
            # Run docker stats for 10 seconds and collect samples
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode != 0:
                return {"test": "docker_resources", "error": "docker_stats_failed"}

            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        container_data = json.loads(line)
                        # Extract CPU and memory percentages
                        cpu_str = container_data.get("CPUPerc", "0%").rstrip("%")
                        mem_str = container_data.get("MemPerc", "0%").rstrip("%")

                        containers.append({
                            "name": container_data.get("Name"),
                            "cpu_percent": float(cpu_str) if cpu_str != "N/A" else 0.0,
                            "mem_percent": float(mem_str) if mem_str != "N/A" else 0.0,
                            "mem_usage": container_data.get("MemUsage", "N/A"),
                            "net_io": container_data.get("NetIO", "N/A")
                        })
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Warning: Failed to parse docker stats line: {e}")
                        continue

            metrics = {
                "test": "docker_resources",
                "containers": containers,
                "max_cpu_threshold": 80,
                "max_mem_threshold": 80,
                "cpu_within_limits": all(c["cpu_percent"] < 80 for c in containers),
                "mem_within_limits": all(c["mem_percent"] < 80 for c in containers)
            }

            print(f"✓ Monitored {len(containers)} containers")
            for container in containers:
                status = "✓" if container["cpu_percent"] < 80 and container["mem_percent"] < 80 else "⚠️"
                print(f"  {status} {container['name']}: CPU {container['cpu_percent']:.1f}%, MEM {container['mem_percent']:.1f}%")

            self.results["tests"].append(metrics)
            return metrics

        except Exception as e:
            print(f"❌ Docker resource monitoring failed: {e}")
            return {"test": "docker_resources", "error": str(e)}

    def test_redis_connectivity(self) -> Dict[str, Any]:
        """
        Test Redis connectivity and basic performance.

        Returns:
            Dictionary with Redis performance metrics
        """
        print("\n📊 Testing Redis connectivity...")

        try:
            # Test Redis ping command
            result = subprocess.run(
                ["docker", "exec", "transfer2read-redis", "redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=5
            )

            redis_available = result.returncode == 0 and "PONG" in result.stdout

            # Test queue depth
            queue_result = subprocess.run(
                ["docker", "exec", "transfer2read-redis", "redis-cli", "LLEN", "celery"],
                capture_output=True,
                text=True,
                timeout=5
            )

            queue_depth = int(queue_result.stdout.strip()) if queue_result.returncode == 0 else -1

            metrics = {
                "test": "redis_connectivity",
                "redis_available": redis_available,
                "queue_depth": queue_depth,
                "max_queue_depth_threshold": 100,
                "queue_within_limits": queue_depth < 100 if queue_depth >= 0 else None
            }

            if redis_available:
                print(f"✓ Redis: Available")
                print(f"✓ Queue depth: {queue_depth} (target: <100) - {'PASS' if queue_depth < 100 else 'FAIL'}")
            else:
                print(f"❌ Redis: Unavailable")

            self.results["tests"].append(metrics)
            return metrics

        except Exception as e:
            print(f"❌ Redis connectivity test failed: {e}")
            return {"test": "redis_connectivity", "error": str(e)}

    def test_database_connectivity(self) -> Dict[str, Any]:
        """
        Test database connectivity via health endpoint.

        Returns:
            Dictionary with database connectivity status
        """
        print("\n📊 Testing database connectivity...")

        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)

            if response.status_code == 200:
                health_data = response.json()
                db_connected = health_data.get("database") == "connected"
                redis_connected = health_data.get("redis") == "connected"

                metrics = {
                    "test": "database_connectivity",
                    "database_connected": db_connected,
                    "redis_connected": redis_connected,
                    "health_status": health_data.get("status")
                }

                print(f"✓ Database: {'Connected' if db_connected else 'Disconnected'}")
                print(f"✓ Redis: {'Connected' if redis_connected else 'Disconnected'}")

                self.results["tests"].append(metrics)
                return metrics
            else:
                return {"test": "database_connectivity", "error": "health_check_failed"}

        except Exception as e:
            print(f"❌ Database connectivity test failed: {e}")
            return {"test": "database_connectivity", "error": str(e)}

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all performance baseline tests.

        Returns:
            Complete test results
        """
        print("=" * 60)
        print("PERFORMANCE BASELINE TESTS")
        print("=" * 60)

        # Test 1: Health endpoint performance
        self.test_health_endpoint_performance(num_requests=100)

        # Test 2: Docker resource usage
        self.test_docker_resource_usage()

        # Test 3: Redis connectivity
        self.test_redis_connectivity()

        # Test 4: Database connectivity
        self.test_database_connectivity()

        print("\n" + "=" * 60)
        print("BASELINE TESTS COMPLETE")
        print("=" * 60)

        return self.results

    def save_results(self, output_path: Path):
        """Save test results to JSON file."""
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to: {output_path}")

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values."""
        sorted_data = sorted(data)
        index = (percentile / 100) * len(sorted_data)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[min(int(index) + 1, len(sorted_data) - 1)]
            return (lower + upper) / 2


if __name__ == "__main__":
    # Run performance baseline tests
    baseline = PerformanceBaseline(base_url="http://localhost:8000")
    results = baseline.run_all_tests()

    # Save results
    # Go up from backend/tests/load to project root, then to docs/sprint-artifacts
    output_dir = Path(__file__).parent.parent.parent.parent / "docs" / "sprint-artifacts"
    output_file = output_dir / f"load-test-baseline-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    baseline.save_results(output_file)

    print("\nNext steps:")
    print("1. Review baseline results in:", output_file)
    print("2. Run full load tests with: locust -f tests/load/scenarios.py --host http://localhost:8000")
    print("3. Generate comprehensive load test report")
