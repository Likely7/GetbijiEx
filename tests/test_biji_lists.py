import pytest

from scripts import biji_export


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise biji_export.requests.exceptions.HTTPError(response=self)

    def json(self):
        return self._payload


def make_topics_payload(names):
    return {
        "c": [
            {
                "id": i,
                "id_alias": f"alias{i}",
                "name": name,
                "extend_data": {"all_resource_count": i * 10},
            }
            for i, name in enumerate(names, start=1)
        ]
    }


def test_list_topics_merges_mine_and_subscribed(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(url)
        if "topic/mine/list" in url:
            return FakeResponse(make_topics_payload(["我的库"]))
        if "subscribe/topic/list" in url:
            return FakeResponse({"c": {"list": make_topics_payload(["订阅的库"])["c"]}})
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(biji_export.requests, "get", fake_get)
    monkeypatch.setattr(biji_export, "get_headers", lambda force_reload=False: {})

    topics = biji_export.list_topics()
    assert [t["name"] for t in topics] == ["我的库", "订阅的库"]
    assert topics[0]["source"] == "mine"
    assert topics[1]["source"] == "sub"
    assert topics[0]["id_alias"] == "alias1"
    assert topics[0]["count"] == 10


def test_list_topics_auth_expired(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None):
        return FakeResponse({"message": "LoginRequired"})

    monkeypatch.setattr(biji_export.requests, "get", fake_get)
    monkeypatch.setattr(biji_export, "get_headers", lambda force_reload=False: {})

    with pytest.raises(biji_export.AuthError):
        biji_export.list_topics()


def test_list_follows_paginates(monkeypatch):
    pages = {
        1: {
            "c": {
                "has_next": True,
                "list": [
                    {
                        "id": 101,
                        "topic_id": 2013364,
                        "name": "博主A",
                        "platform": "DOUYIN",
                        "extend_data": {"get_note_count": 24},
                    }
                ],
            }
        },
        2: {
            "c": {
                "has_next": False,
                "list": [
                    {
                        "id": 102,
                        "topic_id": 2013364,
                        "name": "博主B",
                        "platform": "DOUYIN",
                        "extend_data": {"get_note_count": 5},
                    }
                ],
            }
        },
    }

    def fake_get(url, headers=None, params=None, timeout=None):
        return FakeResponse(pages[params["page"]])

    monkeypatch.setattr(biji_export.requests, "get", fake_get)
    monkeypatch.setattr(biji_export, "get_headers", lambda force_reload=False: {})

    follows = biji_export.list_follows("eYzGqM30")
    assert [f["name"] for f in follows] == ["博主A", "博主B"]
    assert follows[0]["follow_id"] == 101
    assert follows[0]["topic_id"] == 2013364
    assert follows[0]["note_count"] == 24
    assert follows[1]["platform"] == "DOUYIN"


def test_list_follows_auth_expired(monkeypatch):
    def fake_get(url, headers=None, params=None, timeout=None):
        return FakeResponse({"message": "LoginRequired"})

    monkeypatch.setattr(biji_export.requests, "get", fake_get)
    monkeypatch.setattr(biji_export, "get_headers", lambda force_reload=False: {})

    with pytest.raises(biji_export.AuthError):
        biji_export.list_follows("eYzGqM30")
