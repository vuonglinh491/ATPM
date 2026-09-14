from analyzer.product_analyzer import ProductAnalyzer


VALID_PRODUCT = {
    "id": "P001",
    "name": "Camera Wifi",
    "category": "Camera",
    "price": 1_500_000,
    "stock": 20,
    "discount": 10,
    "rating": 4.5,
    "description": "Camera giam sat wifi",
}


def test_valid_product_is_analyzed():
    result = ProductAnalyzer().analyze(VALID_PRODUCT)
    assert result["valid"] is True
    assert result["final_price"] == 1_350_000
    assert result["inventory_value"] == 30_000_000
    assert result["errors"] == []


def test_malformed_json_is_reported():
    result = ProductAnalyzer().analyze_json('{"id":')
    assert result["valid"] is False
    assert "Malformed JSON" in result["errors"][0]
