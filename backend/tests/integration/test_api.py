"""REST API integration tests."""


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert body["mcp_endpoint"] == "/mcp"
    assert body["schema_version"] == "2"


def test_search_orders(client):
    res = client.get(
        "/api/v1/orders/search",
        params={"q": "headphones"},
        headers={"X-User-Id": "demo-user-1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data_provenance"] == "demo"
    assert any(row["id"] == "ord-headphones" for row in body["results"])
    assert all("DEMO" in row["merchant_name"] for row in body["results"])


def test_orders_are_paginated_and_scoped(client):
    headers = {"X-User-Id": "demo-user-1"}
    page = client.get("/api/v1/orders", params={"limit": 1, "offset": 0}, headers=headers)
    assert page.status_code == 200
    body = page.json()
    assert body["limit"] == 1
    assert len(body["items"]) == 1
    assert body["total"] >= 5

    hidden = client.get("/api/v1/orders/ord-headphones", headers={"X-User-Id": "other-user-9"})
    assert hidden.status_code == 404
    assert hidden.json()["detail"]["code"] == "not_found"

    missing = client.get("/api/v1/orders/does-not-exist", headers=headers)
    assert missing.status_code == 404


def test_search_hides_other_users_orders(client):
    res = client.get(
        "/api/v1/orders/search",
        params={"q": "hidden other-user"},
        headers={"X-User-Id": "demo-user-1"},
    )
    assert res.status_code == 200
    assert res.json()["results"] == []


def test_policies_are_labeled_hypothetical(client):
    res = client.get("/api/v1/policies")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 3
    assert all(item["is_hypothetical"] for item in body["items"])
    assert all("DEMO" in item["merchant_name"] for item in body["items"])


def test_policy_and_case_flow(client):
    headers = {"X-User-Id": "demo-user-1"}
    eval_res = client.post(
        "/api/v1/policy/evaluate",
        headers=headers,
        json={
            "order_item_id": "item-headphones",
            "issue_type": "unwanted",
            "issue_description": "DEMO unused gift",
        },
    )
    assert eval_res.status_code == 200
    payload = eval_res.json()
    assert payload["outcome"] == "ELIGIBLE"
    assert payload["applicable_rule_code"] == "DEMO-HA-RETURN-30"

    case_res = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "order_id": "ord-headphones",
            "order_item_id": "item-headphones",
            "issue_type": "unwanted",
            "issue_description": "DEMO unused gift",
            "eligibility_outcome": "ELIGIBLE",
            "policy_rule_id": "rule-harbor-return-30",
        },
    )
    assert case_res.status_code == 200
    case_id = case_res.json()["id"]

    events = client.get(f"/api/v1/cases/{case_id}/events", headers=headers)
    assert events.status_code == 200
    assert any(event["event_type"] == "case_created" for event in events.json())

    prep = client.post(
        "/api/v1/cases/actions/prepare",
        headers=headers,
        json={"case_id": case_id, "action_type": "return_request"},
    )
    assert prep.status_code == 200
    token = prep.json()["confirmation_token"]
    action_id = prep.json()["action_id"]

    denied = client.post(
        "/api/v1/cases/actions/confirm",
        headers=headers,
        json={
            "case_id": case_id,
            "action_id": action_id,
            "confirmation_token": token,
            "user_confirmed": False,
        },
    )
    assert denied.status_code == 400
    assert denied.json()["detail"]["code"] == "confirmation_required"

    confirmed = client.post(
        "/api/v1/cases/actions/confirm",
        headers=headers,
        json={
            "case_id": case_id,
            "action_id": action_id,
            "confirmation_token": token,
            "user_confirmed": True,
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["submission_status"] == "demo_only"

    follow_ups = client.get(f"/api/v1/cases/{case_id}/follow-ups", headers=headers)
    assert follow_ups.status_code == 200
    task_id = follow_ups.json()[0]["id"]
    done = client.post(f"/api/v1/cases/{case_id}/follow-ups/{task_id}/complete", headers=headers)
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
