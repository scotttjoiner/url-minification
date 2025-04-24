# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

from flask_restx import reqparse

"""
Base Parser
"""
get_parser = reqparse.RequestParser()
get_parser.add_argument(
    "Authorization",
    type=str,
    location="headers",
    required=True,
    help='Bearer Token'
)


"""
Search Parser
"""
search_parser = get_parser.copy()
search_parser.add_argument(
    "url",
    type=str,
    location="args",
    required=False,
    help='All or part of a URL'
)
search_parser.add_argument(
    "tag",
    type=str,
    dest="tags",
    location="args",
    action="append",
    required=False,
    help='All or part of a tag.'
)
search_parser.add_argument(
    "page",
    type=int,
    location="args",
    required=False,
    help='Zero based page index. Defaults to 0'
)
search_parser.add_argument(
    "max",
    type=int,
    location="args",
    required=False,
    help='Maximum number of results to return. Defaults to 20.'
)

"""
Page Parser
"""
click_parser = get_parser.copy()
search_parser.add_argument(
    "tag",
    type=str,
    dest="args",
    location="args",
    action="append",
    required=False,
    help='An URL argument value.'
)
click_parser.add_argument(
    "page",
    type=int,
    location="args",
    required=False,
    help='Zero based page index. Defaults to 0'
)
click_parser.add_argument(
    "max",
    type=int,
    location="args",
    required=False,
    help='Maximum number of results to return. Defaults to 20.'
)
