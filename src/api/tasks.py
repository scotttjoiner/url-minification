# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

import requests
from src.celery_app import celery
from celery import Task

class WebhookTask(Task):
    
    # These need to be refactored into settings.py
    autoretry_for = (requests.RequestException,)
    retry_backoff = True          # exponential backoff
    retry_backoff_max = 600       # cap backoff at 10m
    retry_jitter = True           # add some randomness
    max_retries = 5

@celery.task(base=WebhookTask, bind=True)
def send_click_webhook(self, webhook_url: str, payload: dict):
    """
    POSTs to a webhook URL.
    Retries automatically on network errors up to max_retries.
    """
    response = requests.post(webhook_url, json=payload, timeout=5)
    response.raise_for_status()
    return response.text