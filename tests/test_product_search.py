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


def test_search_by_sku_returns_exact_match(client, seed_products):
    response = client.get(
        "/api/v1/products/search",
        params={"sku": "WDG-001"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "WDG-001"
    assert data["items"][0]["title"] == "Widget Pro"


def test_search_by_price_range(client, seed_products):
    response = client.get(
        "/api/v1/products/search",
        params={"min_price": "20", "max_price": "30"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["sku"] == "WDG-001"
    assert data["items"][0]["price"] == "29.99"


def test_search_by_category_id(client, seed_products):
    electronics_id = seed_products["electronics"].id

    response = client.get(
        "/api/v1/products/search",
        params={"category_id": electronics_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["category_id"] == electronics_id for item in data["items"])


def test_search_without_filters_returns_all_products(client, seed_products):
    response = client.get("/api/v1/products/search")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 4
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_search_with_no_matches_returns_empty_items(client, seed_products):
    response = client.get(
        "/api/v1/products/search",
        params={"title": "nonexistent-product"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_search_combined_title_and_category_filters(client, seed_products):
    electronics_id = seed_products["electronics"].id

    response = client.get(
        "/api/v1/products/search",
        params={"title": "Widget", "category_id": electronics_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["category_id"] == electronics_id for item in data["items"])
    assert all("Widget" in item["title"] for item in data["items"])


def test_search_unknown_category_returns_400(client, seed_products):
    response = client.get(
        "/api/v1/products/search",
        params={"category_id": 999},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Category not found"


def test_search_pagination(client, seed_products):
    response = client.get(
        "/api/v1/products/search",
        params={"limit": 1, "offset": 1, "sort_by": "title", "sort_order": "asc"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 1
    assert data["limit"] == 1
    assert data["offset"] == 1
    # title asc: Dev Laptop, Python Guide, Widget Basic, Widget Pro
    assert data["items"][0]["title"] == "Python Guide"
