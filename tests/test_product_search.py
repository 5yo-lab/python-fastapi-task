def test_search_by_title_returns_matching_products(client, seed_products):
    response = client.get(
        "/api/v1/products/search",
        params={"title": "Widget"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 10
    assert data["offset"] == 0

    titles = [item["title"] for item in data["items"]]
    assert "Widget Pro" in titles
    assert "Widget Basic" in titles
    assert "Python Guide" not in titles
