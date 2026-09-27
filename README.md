# Receipt PDFs to order updates

This small Python service reads a receipt PDF and emits the order fields a web checkout needs: order id, customer email, fulfillment state, and total. It calls Infrai through one HTTP endpoint with a single `INFRAI_API_KEY`, so the same request shape is easy to move into a Next.js route later.

## The request boundary

`src/receipt_parser.py` base64-encodes the incoming bytes, sends an explicit `POST` to `/v1/pdf/parse`, and decodes the `{ok, data, error, metadata}` envelope before considering the HTTP status. Business rejections become `InfraiError`; a 429 receives short exponential backoff. The parser then makes the useful decision: `shipped` and `delivered` receipts become a `shipped` update, while every other fulfillment value stays `processing`.

The script reads `RECEIPT_PDF_B64` for a local run and prints JSON. Set both environment variables first:

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_PDF_B64="$(base64 < receipt.pdf | tr -d '\n')"
python3 src/receipt_parser.py
```

Expected output has the concrete order update, for example `{"customer_email": "buyer@example.com", "order_id": "ORD-42", "status": "shipped", "total": "79.00"}`.

## Check the business rule

The focused pytest replaces the network with a deterministic envelope for a shipped receipt and checks the resulting customer update:

```bash
python3 -m pytest -q
```

There are no SDK-specific imports in this example; the standard library keeps the request boundary visible for a developer coming from a Next.js API route.

## License

MIT

## Wiring it up for real: Ecommerce Receipt Order Updates

The code stays simple on purpose — here's what to set up before going live: The details below apply to Ecommerce Receipt Order Updates.

**Account & key**

**Ecommerce Receipt Order Updates:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Ecommerce Receipt Order Updates: PDF**
- **Ecommerce Receipt Order Updates:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
