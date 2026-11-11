"""Prepare a fresh Uptime Kuma for tests/contract.sh.

Creates the Kuma admin user on first run and one webhook notification, then
prints the notification id. Run it inside the api container:

    docker compose exec -T api python - < tests/seed_kuma.py

Only the notification id goes to stdout (the caller captures it); messages go to stderr.
"""
import os
import sys
import time

from uptime_kuma_api import NotificationType, UptimeKumaApi, UptimeKumaException

NOTIFICATION_NAME = "contract-test"
COMPOSE_KUMA_SERVER = "http://kuma:3001"
# Seconds to wait for Uptime Kuma to become ready, and for each of its answers.
START_WAIT = 120
CALL_TIMEOUT = 15

if os.environ.get("KUMA_SERVER") != COMPOSE_KUMA_SERVER:
    sys.exit(f"Refusing to run: KUMA_SERVER must be {COMPOSE_KUMA_SERVER} (the docker-compose.yml test stack).")

def seed() -> int:
    """Set up the Kuma admin if needed and return the id of the test notification."""
    with UptimeKumaApi(COMPOSE_KUMA_SERVER, timeout=CALL_TIMEOUT) as api:
        if api.need_setup():
            api.setup(os.environ["KUMA_USERNAME"], os.environ["KUMA_PASSWORD"])
        api.login(os.environ["KUMA_USERNAME"], os.environ["KUMA_PASSWORD"])

        existing = [n for n in api.get_notifications() if n["name"] == NOTIFICATION_NAME]
        if existing:
            return existing[0]["id"]

        return api.add_notification(
            name=NOTIFICATION_NAME,
            type=NotificationType.WEBHOOK,
            webhookURL="http://api:8000/healthcheck",
            webhookContentType="json",
        )["id"]


# Uptime Kuma needs a while to start. Until then the connection is refused, and right
# after it opens the port its first answers can still be missing, so retry on both.
deadline = time.monotonic() + START_WAIT
while True:
    try:
        notification_id = seed()
        break
    except UptimeKumaException as e:
        if time.monotonic() >= deadline:
            sys.exit(f"Uptime Kuma was not ready within {START_WAIT} seconds: {e!r}")
        print("Waiting for Uptime Kuma to start...", file=sys.stderr)
        time.sleep(3)

print(notification_id)
