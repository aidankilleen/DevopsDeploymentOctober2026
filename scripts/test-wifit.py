#!/usr/bin/env python3

import time
import urllib.request
import statistics

# Cloudflare test-file endpoint
DOWNLOAD_URL = "https://speed.cloudflare.com/__down?bytes=10000000"
DOWNLOAD_BYTES = 10_000_000

# Small request used to estimate HTTP latency
LATENCY_URL = "https://www.cloudflare.com/cdn-cgi/trace"


def test_latency(runs=5):
    results = []

    print("Testing latency...")

    for _ in range(runs):
        start = time.perf_counter()

        try:
            with urllib.request.urlopen(LATENCY_URL, timeout=10) as response:
                response.read(1)

            elapsed_ms = (time.perf_counter() - start) * 1000
            results.append(elapsed_ms)

        except Exception as exc:
            print(f"Latency test failed: {exc}")

    return statistics.median(results) if results else None


def test_download():
    print("Testing download speed...")

    start = time.perf_counter()
    downloaded = 0

    try:
        with urllib.request.urlopen(DOWNLOAD_URL, timeout=30) as response:
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                downloaded += len(chunk)

        elapsed = time.perf_counter() - start

        # Convert bytes/sec -> megabits/sec
        mbps = (downloaded * 8) / elapsed / 1_000_000
        return mbps, downloaded, elapsed

    except Exception as exc:
        print(f"Download test failed: {exc}")
        return None, 0, 0


def main():
    print("\n=== Wi-Fi / Internet Speed Test ===\n")

    latency = test_latency()
    speed, downloaded, elapsed = test_download()

    print("\n--- Results ---")

    if latency is not None:
        print(f"Latency:       {latency:.1f} ms")
    else:
        print("Latency:       unavailable")

    if speed is not None:
        print(f"Download:      {speed:.1f} Mbps")
        print(f"Data received: {downloaded / 1_000_000:.1f} MB")
        print(f"Test duration: {elapsed:.1f} seconds")
    else:
        print("Download:      unavailable")


if __name__ == "__main__":
    main()