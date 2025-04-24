# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

from flask_restx import fields
from .restplus import rest_api

new_link_request = rest_api.model('Minification Request', {
    'url': fields.String(
        required=True,
        description='The URL to be minimized. It may contain placeholders for query or REST-style parameters.',
        example='https://test.com?param1={0}&param2={1}'
    ),
    'short_link': fields.String(
        required=False,
        description='The requested shortend link.',
        example='myshorturl'
    ),
    'expiration': fields.DateTime(
        required=False,
        default=None,
        description='Date (in UTC) after which minified URL will stop working. Empty string for no expiration',
        nullable=True
    ),
    'simpleTracking': fields.Boolean(
        required=False,
        default=True,
        description='Click tracking records last access only'
    ),
    'clickHook': fields.String(
        required=False,
        description='A URL to recieve click notifications via POST',
        example='https://test.com/clickhook'
    ),
    'tags': fields.List(
        fields.String,
        required=False,
        default=[],
        description='A list of tags. May be an empty array',
        example=["tag1", "tag2", "tag3"]
    )
})

update_link_request = rest_api.model('Update Link Request', {
    'url': fields.String(
        required=False,
        description='The URL to be minimized. It may contain placeholders for query or REST-style parameters.',
        example='https://test.com?param1={0}&param2={1}'
    ),
    'expiration': fields.DateTime(
        required=False,
        default=None,
        description='Date (in UTC) after which minified URL will stop working. Empty string for no expiration',
        nullable=True
    ),
    'simpleTracking': fields.Boolean(
        required=False,
        default=True,
        description='Click tracking records last access only'
    ),
    'clickHook': fields.String(
        required=False,
        description='A URL to recieve click notifications via POST',
        example='https://test.com/clickhook'
    ),
    'tags': fields.List(
        fields.String,
        required=False,
        default=[],
        description='A list of tags. May be an empty array',
        example=["tag1", "tag2", "tag3"]
    )
})

link_object = rest_api.model('Link Object', {
    'id': fields.String(attribute='_id'),
    'url': fields.String,
    'short_link': fields.String,
    'created': fields.DateTime,
    'updated': fields.DateTime,
    'expiration': fields.DateTime,
    'clicked': fields.DateTime,
    'simpleTracking': fields.Boolean,
    'clickHook': fields.String,
    'tags': fields.List(fields.String)
})

click_object = rest_api.model('Click Object', {
    'id': fields.String(attribute='_id' ),
    'url_id': fields.String,
    'clicked': fields.DateTime,
    'request_url': fields.String,
    'args': fields.List(fields.String)
})
