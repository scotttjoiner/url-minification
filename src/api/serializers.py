# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

from flask_restx import fields
from .extensions import ns

new_link_request = ns.model('Minification Request', {
    'redirect_url': fields.String(
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
    'web_hook': fields.String(
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

update_link_request = ns.model('Update Link Request', {
    'redirect_url': fields.String(
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
    'web_hook': fields.String(
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

_link_hateoas = ns.model('LinkHateoas', {
    'self':   fields.String(description='This resource’s URL'),
    'clicks': fields.String(description='URL to fetch click list')
})

link_object = ns.model('Link', {
    'id':           fields.String(attribute='_id'),
    'short_link':   fields.String(),
    'redirect_url': fields.String(),
    'web_hook': fields.String,
    'click_count':  fields.Integer(),
    'last_clicked': fields.DateTime(),
    'created':      fields.DateTime(),
    'updated':      fields.DateTime(),
    'expiration':   fields.DateTime(),
    #'active':       fields.Boolean(),
    'owner':        fields.String(description='ID of the user who created this link'),
    'tags':         fields.List(fields.String()),
    '_links':       fields.Nested(_link_hateoas, attribute='_links')
})

click_object = ns.model('Click', {
    'id':          fields.String(attribute='_id'),
    'url_id':      fields.String(),
    'clicked':     fields.DateTime(),
    'request_url': fields.String(),
    'args':        fields.List(fields.String()),
    'ip_address':  fields.String(),
    'user_agent':  fields.String(),
    'referrer':    fields.String(),
})