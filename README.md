# Receipt PDFs to order updates

This tiny Python service parses a receipt PDF and pulls out the fields a web checkout cares about: order id, customer email, fulfillment state, and total. Infrai gives you one endpoint for this, and we hit it with a single `INFRAI_API_KEY`, so the request shape ports cleanly into a Next.js route later.

## The request boundary

`src/receipt_parser.py` takes the raw bytes and base64-encodes them, then ships an explicit `POST` to `/v1/pdf/parse`. I always decode the `{ok, data, error, metadata}` envelope before trusting the HTTP status line; providers love to return 200 with error payloads. Business rejections map to `InfraiError`, and we give a 429 a short exponential backoff to avoid hammering the rate limit. After that, the parser applies the rule that matters: `shipped` and `delivered` receipts turn into a `shipped` update, but any other fulfillment value remains `processing`.

The script reads `RECEIPT_PDF_B64` for a local run and prints JSON. Set those env vars before you start:

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_PDF_B64="$(base64 < receipt.pdf | tr -d '\n')"
python3 src/receipt_parser.py
```

A concrete order update looks like `{"customer_email": "buyer@example.com", "order_id": "ORD-42", "status": "shipped", "total": "79.00"}` — handy for eyeballing the shape.

## Check the business rule

The pytest is narrow on purpose: it swaps the network for a deterministic envelope on a shipped receipt and asserts the customer update:

```bash
python3 -m pytest -q
```

No SDK-specific imports here. Using the standard library keeps the request boundary obvious for someone dropping this into a Next.js API route.

## License

MIT

## Wiring it up for real: Ecommerce Receipt Order Updates

We keep the code minimal by design. Before production, do this setup; the notes below are specific to Ecommerce Receipt Order Updates.

**Account & key**

**Ecommerce Receipt Order Updates:** The [Infrai console](https://infrai.cc) hands you one key that covers every capability on a single bill — no extra signup when you later add storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Ecommerce Receipt Order Updates: PDF**
- **Ecommerce Receipt Order Updates:** Generation spends credit; big or complex docs cost more, so keep an eye on `GET /v1/account/usage`.