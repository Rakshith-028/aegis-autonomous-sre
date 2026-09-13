import time

import requests


TARGET = "http://localhost:8001/"
REQUEST_DELAY_SECONDS = 0.25


def main() -> None:
    total = 0

    print("AEGIS LOAD GENERATOR")
    print(f"Target: {TARGET}")
    print("Press Ctrl+C to stop.")
    print()

    try:
        while True:
            try:
                response = requests.get(
                    TARGET,
                    timeout=3,
                )

                total += 1

                if total % 20 == 0:
                    print(
                        f"Requests sent: {total} | "
                        f"Last status: {response.status_code}"
                    )

            except requests.RequestException as error:
                print(f"Request failed: {error}")

            time.sleep(REQUEST_DELAY_SECONDS)

    except KeyboardInterrupt:
        print(f"\nStopped. Total requests: {total}")


if __name__ == "__main__":
    main()
