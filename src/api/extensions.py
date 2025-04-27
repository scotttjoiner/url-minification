# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

from flask_pymongo import PyMongo
from flask_restx import Namespace
from flask import url_for
from functools import wraps

# instantiate but don’t init yet
mongo = PyMongo()

# To prevent circular references
ns = Namespace(
    'Links', 
    description='URL shortening operations'
)

# Exceptions
class LinkNotFoundError(Exception):
    pass

class LinkExpiredError(Exception):
    pass

def attach_hateoas(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1) Call the original handler
        resp = f(*args, **kwargs)

        # 2) Normalize into data, status, headers
        data = None
        status = None
        headers = None

        if isinstance(resp, tuple):
            length = len(resp)
            data = resp[0] if length >= 1 else None
            status = resp[1] if length >= 2 else None
            headers = resp[2] if length >= 3 else None
        else:
            data = resp

        # 3) Attach links to every dict with an '_id'
        def _attach(doc):
            if isinstance(doc, dict) and 'short_link' in doc:
                sid = str(doc['short_link'])
                doc.setdefault('_links', {})
                doc['_links'].update({
                    'self':   url_for('api.links_item',  id=sid, _external=False),
                    'clicks': url_for('api.link_clicks', id=sid, _external=False),
                })
            return doc

        if isinstance(data, list):
            data = [_attach(d) for d in data]
        else:
            data = _attach(data)

        # 4) Rebuild the original return shape
        out = ()
        if data is not None:
            out += (data,)
        if status is not None:
            out += (status,)
        if headers is not None:
            out += (headers,)

        if not out:
            return None
        if len(out) == 1:
            return out[0]
        return out

    return decorated