# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

import hashlib
import logging
from typing import Optional
from src.celery_app import celery

from datetime import datetime, timezone
from dateutil.parser import parse
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_restx import marshal
from flask import request

from .extensions import mongo, LinkNotFoundError, LinkExpiredError
from .serializers import new_link_request, update_link_request
from .tasks import send_click_webhook

log = logging.getLogger(__name__)

def generate_short_link():
    """
    Generate a potential short_link candidate using a new ObjectId and MD5.
    Iterates through candidate lengths from 5 to 11.
    """
    new_id = ObjectId()
    id_string = str(new_id).encode('utf-8')
    for i in range(5, 12):
        yield hashlib.md5(id_string).hexdigest()[:i]


def insert_unique_short_link(url_data):
    """
    Atomic insert leveraging mongoDB's atomicity and unique index inforcement
    """
    generate_link = not url_data.get('short_link')
    max_attempts = 5 if generate_link else 1
    
    for _ in range(max_attempts):
        if (generate_link):
            candidate = next(generate_short_link()) 
            url_data['short_link'] = candidate
        try:
            mongo.db.links.insert_one(url_data)
            return
        except DuplicateKeyError:
            continue

    raise Exception("Failed to generate a unique short_link after several attempts.")

      
def create_link(data):
    """
    Generate and save a new minified url in the database for each URL in the request
    """

   # Get a dictionary
    links = marshal(data, new_link_request, ordered=True)
    
    for link in links:

        # If they haven't provied a url, just move on
        if not link.get('redirect_url'):
            continue

        # Add some data
        now = datetime.now(timezone.utc)
        link['created'] = now
        link['updated'] = now
        link['expiration'] = None if not link['expiration'] else parse(link['expiration'])
        link['owner'] =  request.decoded_token.get('sub')
        link['click_count'] = 0

        # If they passed us a custom short_link, try to use it
        if link.get('short_link'):
            if mongo.db.links.find_one({'short_link': link['short_link']}):
                log.warning(f"Requested short link {link['short_link']} is not available. Defaulting to generated link")
                # Conflict: Remove provided short_link to generate a new one.
                link.pop('short_link', None)
            
        # Can this be feactored to insert_many?
        try:
            insert_unique_short_link(link)
        except Exception as ex:
            log.error(str(ex))

    return links


def update_link(url_id, data):
    """
    Update a minified URL in the database.

    :param url_id: The unique identifier of the URL to update.
    :param data: A dictionary with the update information.
    :return: The updated URL record.
    """
    # Normalize empty expiration strings to None
    if data.get('expiration') == '':
        data['expiration'] = None

    # Validate and sanitize the incoming data
    validated_data = marshal(data, update_link_request)

    # Prepare the update document using MongoDB update operators.
    updates = {
        '$currentDate': {'updated': True},
        '$set': {}
    }

    # List of fields to update directly
    fields = ['url', 'expiration', 'web_hook', 'tags']

    for field in fields:
        if field in validated_data:
            updates['$set'][field] = validated_data[field]

    # Process expiration field with additional parsing logic
    if 'expiration' in validated_data:
        updates['$set']['expiration'] = (
            parse(validated_data['expiration'])
            if validated_data['expiration'] else None
        )

    # Perform the update
    mongo.db.links.update_one({"_id": ObjectId(url_id)}, updates)

    # Retrieve and return the updated document, raising an error if not found.
    return mongo.db.links.find_one_or_404({"_id": ObjectId(url_id)})

def delete_link(id):
    """
    Deletes a link if it exists
    """

    mongo.db.links.find_one_or_404({"_id": ObjectId(id)})
    mongo.db.links.delete_one({"_id": ObjectId(id)})

     
def find_one(id):
    """
    Locate a minified url in the database
    """

    # Dynamically buld the filter
    s = {}

    if ObjectId.is_valid(id):
        s['_id'] = ObjectId(id)
    else:
        s['short_link'] = id

    return mongo.db.links.find_one_or_404(s)


def search(args):
    """
    Search for url in the database
    """

    url = args.get('url')
    tags = args.getlist('tag')
    max = int(args.get('max') or 20)
    page = int(args.get('page') or 0) * max

    # Dynamically build the query
    s = {}

    if len(tags):
        s['tags'] = {"$regex": "|".join(tags), "$options": "i"}

    if url:
        s['url'] = {"$text": {'$search' :url}}
    
    return [x for x in mongo.db.links.find(s).skip(page).limit(max)]


def get_clicks(id, args):
    """
    Click Reporting
    """

    tags = args.getlist('args')
    max = int(args.get('max') or 20)
    page = int(args.get('page') or 0) * max

    url_object = find_one(id)

    # Dynamically build the query
    s = {}

    if url_object:
        s['url_id'] = url_object['_id']

    if len(tags):
        s['args'] = {"$regex": "|".join(tags), "$options": "i"}


    return [x for x in mongo.db.clicks.find(s).skip(page).limit(max)]

def add_link_click(link, requested_link, args):
    """
    Click Tracking:
    1) Increment click_count & set last_clicked on the link doc
    2) Record a full click entry (with IP, UA, Referer)
    3) Fire off the webhook asynchronously
    """
    try:
        # 1) Update link document: bump count & set last_clicked
        updates = {
            '$currentDate': {'last_clicked': True},
            '$inc':         {'click_count': 1},
        }
        mongo.db.links.update_one({'_id': link['_id']}, updates)

        # 2) Collect request context
        click = {
            'url_id':       link['_id'],
            'clicked':      datetime.now(timezone.utc),
            'request_url':  requested_link,
            'args':         args,
            'ip_address':   request.remote_addr,
            'user_agent':   request.headers.get('User-Agent'),
            'referrer':     request.headers.get('Referer'),
        }
              
        # 3) Fire webhook task if configured
        webhook_url = link.get('web_hook')
        if webhook_url and webhook_url != 'https://test.com/webhook':
            send_click_webhook.delay(webhook_url, click)

    except Exception as ex:
        log.exception("Error logging click: %s", ex)


def get_redirect_target(short_link: str, request_url: str, varargs: Optional[str] = None) -> str:
    """
    Main Redirect Logic
    """
    link = find_one(short_link)
    if not link:
        raise LinkNotFoundError(f"No link for {short_link}")

    exp = link.get("expiration")
    if exp and exp.date() < datetime.now(timezone.utc).date():
        raise LinkExpiredError(f"Link {short_link} expired")

    args = varargs.split("/") if varargs else []
    add_link_click(link, request_url, args)

    # this will safely work even if there are no `{}` in the URL
    return link["redirect_url"].format(*args)