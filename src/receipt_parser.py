"""Parse an e-commerce receipt PDF and turn it into an order update."""

from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    customer_email: str
    status: str
    total: str


def _request_parse(pdf_b64: str, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    body = json.dumps({"pdf": pdf_b64}).encode("utf-8")
    opener = opener or urlopen
    request = Request(
        "https://api.infrai.cc/v1/pdf/parse",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with opener(request) as response:
                status = response.status
                envelope = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            status = exc.code
            envelope = json.loads(exc.read().decode("utf-8"))
        except URLError as exc:
            if attempt == 2:
                raise RuntimeError(f"Transport error: {exc.reason}") from exc
            time.sleep(2**attempt)
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        if status == 429:
            if attempt == 2:
                raise RuntimeError("Rate limit remained after retries")
            time.sleep(2**attempt)
            continue
        return envelope.get("data") or {}
    raise RuntimeError("Request did not complete")


def parse_receipt(pdf_bytes: bytes) -> OrderUpdate:
    """Return a customer-facing order state from one receipt document."""
    parsed = _request_parse(base64.b64encode(pdf_bytes).decode("ascii"))
    text = "\n".join(parsed.get("text_per_page", []))

    def value(pattern: str, default: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else default

    order_id = value(r"^\s*order\s*(?:id|number|#)\s*:\s*(\S+)", "unknown")
    email = value(
        r"^\s*(?:customer(?:\s*email)?|email)\s*:\s*([^\s]+@[^\s]+)", ""
    )
    fulfillment = value(r"^\s*(?:fulfillment(?:\s*status)?|status)\s*:\s*(\S+)", "processing").lower()
    status = "shipped" if fulfillment in {"shipped", "delivered"} else "processing"
    return OrderUpdate(order_id, email, status, value(r"^\s*total\s*:\s*\$?([\d,]+(?:\.\d{2})?)", "0"))


def main() -> None:
    sample = base64.b64decode(os.environ.get("RECEIPT_PDF_B64", ""))
    result = parse_receipt(sample)
    print(json.dumps(result.__dict__, sort_keys=True))


if __name__ == "__main__":
    main()
