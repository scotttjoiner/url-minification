# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Scott Joiner

from flask_pymongo import PyMongo
from flask_restx import Namespace

# instantiate but don’t init yet
mongo = PyMongo()

# To prevent circular references
ns = Namespace(
    'Links', 
    description='URL shortening operations'
)
