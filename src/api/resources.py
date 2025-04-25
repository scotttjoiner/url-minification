# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner
 
import logging
from flask import request, abort, redirect
from flask_restx import Resource
from .auth import requires_auth
from .serializers import new_link_request, update_link_request, link_object, click_object
from .parsers import search_parser, get_parser, click_parser
from bson.objectid import ObjectId
from datetime import datetime
from src.api import services as ops
from .extensions import mongo, ns

log = logging.getLogger(__name__)

@ns.route('/')
@ns.response(401, 'Not Authorized.')
@ns.response(500, 'Link error.')
class LinkListResource(Resource):

    @requires_auth
    @ns.expect(search_parser, validate=True)
    @ns.marshal_list_with(link_object, code=200, description='Link list')
    def get(self):
        """
        Search
        """

        try:
            return ops.search(request.args), 200

        except Exception as e:
            abort(500, str(e))


    @requires_auth
    @ns.doc(body=[new_link_request], parser=get_parser, validate=True)
    @ns.marshal_list_with(link_object, code=201, description='Link created')
    def post(self):
        """
        Creates minified links for the provided urls.
        """

        try:
            return ops.create_link(ns.payload), 201

        except Exception as e:
            abort(500, str(e))


@ns.route('/<string:id>')
@ns.response(500, 'URL error.')
@ns.response(401, 'Not Authorized.')
class LinkResource(Resource):

    @requires_auth
    @ns.response(404, 'Link not found.')
    @ns.marshal_with(link_object, code=200, description='Link object')
    @ns.expect(get_parser, validate=True)
    def get(self, id):
        """
        Returns a link object given the identifier.
        """

        try:
            return ops.find_one(id), 200

        except Exception as e:
            abort(404, str(e))


    @requires_auth
    @ns.response(404, 'Linl not found.')
    @ns.doc(body=update_link_request, parser=get_parser, validate=True)
    @ns.marshal_with(link_object, code=200, description='Link updated')
    def put(self, id):
        """
        Updates a link given the identifier.
        """

        try:
            return ops.update_link(id, ns.payload), 200

        except Exception as e:
            abort(404, str(e))


    @requires_auth
    @ns.response(204, 'Link deleted')
    @ns.response(404, 'Link not found.')
    @ns.expect(get_parser, validate=True)
    def delete(self, id):
        """
        Deletes a shortened link given the identifier.
        """

        try:
            mongo.db.urls.find_one_or_404({"_id": ObjectId(id)})
            mongo.db.urls.delete_one({"_id": ObjectId(id)})
            return '', 204

        except Exception as e:
            abort(404, str(e))


@ns.route('/<string:id>/clicks')
@ns.response(500, 'Link error.')
@ns.response(401, 'Not Authorized.')
class ClickListResource(Resource):

    @requires_auth
    @ns.response(404, 'Link not found.')
    @ns.expect(click_parser, validate=True)
    @ns.marshal_list_with(click_object, code=200, description='Link list')
    def get(self, id):
        """
        Returns a Link's clicks based on the search args.
        """

        try:
            return ops.get_clicks(id, request.args), 200

        except Exception as e:
            abort(404, str(e))


@ns.route('/<short_link>/', defaults={'varargs': None})
@ns.route('/<short_link>/<path:varargs>')
class RedirectResource(Resource):

    def redirect_short_link(short_link, varargs):
        """
        Main Redirect Logic
        """

        # 1) Look up the URL doc (assume find_one returns None if missing)
        url_doc = ops.find_one(short_link)
        if not url_doc:
            abort(404, "Invalid Link")

        # 2) Expiration check (assume `expiration` is a datetime or None)
        exp = url_doc.get('expiration')
        if exp and exp.date() < datetime.now(datetime.timezone.utc).date():
            abort(410, "Link Expired")

        # 3) Build args list, log the click
        args = varargs.split('/') if varargs else []
        ops.add_link_click(url_doc, request.url, args)

        # 4) Always safe to format with zero or more args
        target = url_doc['url'].format(*args)
        return redirect(target)