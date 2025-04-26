# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

from celery import Celery
from src import settings

def make_celery(app_name=None):
    return Celery(
        app_name or __name__,
        broker=settings.CELERY_BROKER_URL,
        backend= settings.CELERY_RESULT_BACKEND,
        include=["src.api.tasks"]   
    )

celery = make_celery("link_click_webhook")