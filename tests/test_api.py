# tests/test_link_endpoints.py

import pytest
from bson import ObjectId
from src.app import create_app
from unittest.mock import MagicMock
#from src.api.endpoints import LinkResource, LinkListResource

@pytest.fixture
def app():
    app = create_app()
    # ensure the PyMongo extension has hooked up .db
    with app.app_context():
        # no-op, just enters the context so init_app can finish all setup
        pass
    return app

def test_get_single_link_uses_mongo(monkeypatch, app):
    # 1) Prepare a fake Mongo collection
    fake_doc = {
        "_id": ObjectId("605c5a2f9b1e8f1f08d3c5ab"),
        "short_url": "abc123",
        "url": "https://example.com"
    }
    mock_collection = MagicMock()
    # find_one should return our fake_doc
    mock_collection.find_one.return_value = fake_doc

    # 2) Patch the mongo client used by your API
    #    Adjust the import path to wherever you reference mongo.db.urls
    monkeypatch.setattr(
        'src.api.extensions.mongo.db.urls',
        mock_collection
    )

    client = app.test_client()
    # 3) Hit your endpoint as if a real HTTP GET
    response = client.get(
        '/api/links/abc123',
        headers={'Authorization': 'Bearer valid-token'}
    )

    # 4) Assert it returned our fake_doc JSON and 200
    assert response.status_code == 200
    assert response.get_json() == {
        "_id": "605c5a2f9b1e8f1f08d3c5ab",  # Flask-RESTX will JSONify ObjectId
        "short_url": "abc123",
        "url": "https://example.com"
    }

    # 5) Verify that the code actually called Mongo
    mock_collection.find_one.assert_called_once_with(
        {"_id": ObjectId("605c5a2f9b1e8f1f08d3c5ab")}
    )

def test_search_links_uses_mongo(monkeypatch, app):
    # Fake multiple docs for the list/search endpoint
    fake_list = [
        {"short_url": "a", "url": "u1"},
        {"short_url": "b", "url": "u2"},
    ]
    mock_collection = MagicMock()
    mock_collection.find.return_value = fake_list

    monkeypatch.setattr(
        'src.api.extensions.mongo.db.urls',
        mock_collection
    )

    client = app.test_client()
    response = client.get(
        '/api/links?tag=foo',
        headers={'Authorization': 'Bearer valid-token'}
    )

    assert response.status_code == 200
    assert response.get_json() == fake_list
    # Verify we passed the query args to Mongo
    mock_collection.find.assert_called_once_with({"tag": "foo"})