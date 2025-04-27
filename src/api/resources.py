# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner
 
import logging
from flask import request, abort, redirect
from flask_restx import Resource
from .auth import requires_auth
from .serializers import new_link_request, update_link_request, link_object, click_object
from .parsers import search_parser, get_parser, click_parser
from src.api import services as ops
from .extensions import ns, attach_hateoas

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
    @attach_hateoas
    @ns.expect(get_parser, [new_link_request], validate=True)
    @ns.marshal_list_with(link_object, code=201, description='Link created')
    def post(self):
        """
        Creates minified links for the provided urls.
        """

        try:
            return ops.create_link(ns.payload), 201

        except Exception as e:
            abort(500, str(e))


@ns.route('/<string:id>', endpoint='links_item')
@ns.response(500, 'Link error.')
@ns.response(401, 'Not Authorized.')
class LinkResource(Resource):

    @requires_auth
    @attach_hateoas
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
    @attach_hateoas
    @ns.response(404, 'Link not found.')
    @ns.expect(update_link_request, get_parser, validate=True)
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
            ops.delete_link(id)
            return '', 204

        except Exception as e:
            abort(404, str(e))


@ns.route('/<string:id>/clicks', endpoint='link_clicks')
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
        Main Redirect 
        """

        try:
            target = ops.get_redirect_target(
                short_link,
                request.url,
                varargs
            )
        except ops.LinkNotFoundError as e:
            abort(404, str(e))
        except ops.LinkExpiredError as e:
            abort(410, str(e))

        return redirect(target)