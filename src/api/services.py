# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

import json
import hashlib
import logging
from typing import Optional
import requests

from datetime import datetime, timezone
from dateutil.parser import parse
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_restx import marshal

from .extensions import mongo
from .serializers import new_link_request, update_link_request

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


def insert_unique_short_link(db, url_data):
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
            mongo.db.urls.urls.insert_one(url_data)
            return
        except DuplicateKeyError:
            continue

    raise Exception("Failed to generate a unique short_link after several attempts.")

      
def create_link(data):
    """
    Generate and save a new minified url in the database for each URL in the request
    """

   # Get a dictionary
    urls = marshal(data, new_link_request, ordered=True)

    for url in urls:

        # If they haven't provied a url, just move on
        if not url.get('url'):
            continue

        # Add some data
        now = datetime.now(timezone.utc)
        url['created'] = now
        url['updated'] = now
        url['expiration'] = None if not url['expiration'] else parse(url['expiration'])

        # If they passed us a custom short_link, try to use it
        if url.get('short_link'):
            if mongo.db.urls.find_one({'short_link': url['short_link']}):
                log.warning(f"Requested short link {url['short_link']} is not available. Defaulting to generated link")
                # Conflict: Remove provided short_link to generate a new one.
                url.pop('short_link', None)
            
        # Can this be feactored to insert_many?
        try:
            insert_unique_short_link(url)
        except Exception as ex:
            log.error(str(ex))

    return urls


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
    fields = ['url', 'simpleTracking', 'webhook', 'tags']

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
    mongo.db.urls.update_one({"_id": ObjectId(url_id)}, updates)

    # Retrieve and return the updated document, raising an error if not found.
    return mongo.db.urls.find_one_or_404({"_id": ObjectId(url_id)})

def delete_link(id):
    """
    Deletes a link if it exists
    """

    mongo.db.urls.find_one_or_404({"_id": ObjectId(id)})
    mongo.db.urls.delete_one({"_id": ObjectId(id)})

     
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

    return mongo.db.urls.find_one_or_404(s)


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
    
    return [x for x in mongo.db.urls.find(s).skip(page).limit(max)]


def add_link_click(url, requested_link, args):
    """
    Click Tracking
    """

    try:
        # Updates v2
        updates = {
            '$currentDate': {'clicked': True }
        }

        # Update
        mongo.db.urls.update_one({"_id": url['_id']}, updates)

        # No need to go farther if we're just using simple tracking
        if  url['simpleTracking']:
            return

        click = {
            'url_id': url['_id'],
            'clicked': datetime.now(timezone.utc),
            'request_link': requested_link,
            'args': args
        }

        # Insert
        mongo.db.clicks.insert_one(click)

        post_back = url['webhook']
        if post_back and post_back != 'https://test.com/webhook':
            web_hook(url, click)

    except Exception as ex:

        log.exception(str(ex))


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

def web_hook(url, click):
    """
    Extremely naieve webhook
    """

    try:
        data = {
            'url_id': str(url['_id']),
            'short_link': url['short_link'],
            'clicked': str(click['clicked']),
            'request_link': click['request_link'],
            'args': click['args'],
            'tags': url['tags']
        }
        requests.post(url['webhook'], json=json.dumps(data))

    except Exception as ex:
        log.exception(str(ex))



class LinkNotFoundError(Exception):
    pass

class LinkExpiredError(Exception):
    pass

def get_redirect_target(short_link: str, request_url: str, varargs: Optional[str] = None) -> str:
    """
    Main Redirect Logic
    """
    doc = find_one(short_link)
    if not doc:
        raise LinkNotFoundError(f"No link for {short_link}")

    exp = doc.get("expiration")
    if exp and exp.date() < datetime.now(timezone.utc).date():
        raise LinkExpiredError(f"Link {short_link} expired")

    args = varargs.split("/") if varargs else []
    add_link_click(doc, request_url, args)

    # this will safely work even if there are no `{}` in the URL
    return doc["url"].format(*args)