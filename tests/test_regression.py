from analyzer.product_analyzer import ProductAnalyzer


def test_wrong_types_do_not_crash_analyzer():
    result = ProductAnalyzer().analyze({"id": None, "price": [], "stock": "x"})
    assert result["valid"] is False
    assert result["errors"]


def test_csv_input_is_supported():
    raw = "id,name,category,price,stock,discount,rating\nP1,Phone,Mobile,100,2,0,4"
    result = ProductAnalyzer().analyze_json(raw, "csv")
    assert result["valid"] is True
