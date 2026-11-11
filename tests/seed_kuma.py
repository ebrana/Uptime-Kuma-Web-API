"""Prepare a fresh Uptime Kuma for tests/contract.sh.

Creates the Kuma admin user on first run and one webhook notification, then
prints the notification id. Run it inside the api container:

    docker compose exec -T api python - < tests/seed_kuma.py
"""
import os

from uptime_kuma_api import NotificationType, UptimeKumaApi

NOTIFICATION_NAME = "contract-test"

with UptimeKumaApi(os.environ["KUMA_SERVER"], timeout=90) as api:
    if api.need_setup():
        api.setup(os.environ["KUMA_USERNAME"], os.environ["KUMA_PASSWORD"])
    api.login(os.environ["KUMA_USERNAME"], os.environ["KUMA_PASSWORD"])

    existing = [n for n in api.get_notifications() if n["name"] == NOTIFICATION_NAME]
    if existing:
        notification_id = existing[0]["id"]
    else:
        notification_id = api.add_notification(
            name=NOTIFICATION_NAME,
            type=NotificationType.WEBHOOK,
            webhookURL="http://api:8000/healthcheck",
            webhookContentType="json",
        )["id"]

    print(notification_id)
