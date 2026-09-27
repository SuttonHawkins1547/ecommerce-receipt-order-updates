import json

from src.receipt_parser import parse_receipt


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"ok": True, "data": {
            "pdf_id": "pdf-example",
            "text_per_page": ["Order ID: ORD-42\nCustomer: buyer@example.com\nFulfillment: shipped\nTotal: 79.00"],
        }}).encode()


def test_shipped_receipt_becomes_customer_update(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr("src.receipt_parser.urlopen", lambda request: FakeResponse())
    update = parse_receipt(b"pdf bytes")
    assert update.order_id == "ORD-42"
    assert update.status == "shipped"
    assert update.customer_email == "buyer@example.com"
    assert update.total == "79.00"
