# LedgerGuard AI — Architectural Specification

## 1. System Overview & Monorepo Structure

LedgerGuard AI is built as a high-performance, modular enterprise financial operations platform. It combines a vectorized multi-source reconciliation engine in Python with a Next.js enterprise operations console.

```text
AI Finance Recovery/
├── apps/
│   ├── api/                     # FastAPI Backend Application
│   │   ├── app/
│   │   │   ├── api/v1/          # REST API endpoints (health, datasets, recon, dashboard, exceptions, copilot)
│   │   │   ├── core/            # Database session, config, logging
│   │   │   ├── engine/          # Vectorized matching, rules engine, ML anomaly detector, evidence generator
│   │   │   ├── models/          # SQLAlchemy ORM models with B-Tree indexes
│   │   │   └── services/        # Service layer (audit, dataset, exception, copilot, recon)
│   │   └── tests/               # Pytest suite (18 unit/integration tests)
│   └── web/                     # Next.js 14 Frontend Application
│       ├── src/
│       │   ├── app/             # App Router pages (/, /reconciliation, /exceptions, /reports, /copilot, /methodology, /settings)
│       │   ├── components/      # UI primitives & layout shell (AppShell, Sidebar, Topbar, CommandPalette)
│       │   └── lib/             # API client & INR formatting utilities
├── data/sample/                 # Synthetic 60-day ecommerce financial dataset (2,010 records, 150 anomalies)
├── docs/                        # Architecture specs, Mermaid diagram, demo script, pitch script
├── scripts/                     # Data generator script (generate_data.py)
├── docker-compose.yml           # Multi-container Docker setup
└── README.md                    # Product & technical documentation
```

---

## 2. Multi-Source Ingestion & Data Normalization

LedgerGuard AI ingests four distinct financial feeds:
1. **Orders (ERP)**: 500 orders (₹99 to ₹1,50,000).
2. **Payments (Gateway)**: 540 captured transactions.
3. **Settlements (Bank Advice)**: 470 payout records with UTR references.
4. **Invoices (Vendor Billing)**: 500 tax invoices.

### Normalization Pipeline (`apps/api/app/engine/data_normalizer.py`)
- **Reference Normalization**: Strips spaces and prefixes (`ord_live_1001` → `ORD_1001`).
- **Currency & Amount**: Converts text inputs to float, rounding to 2 decimal places.
- **Timestamp Standardization**: Coerces naive dates into ISO 8601 UTC timestamps.

---

## 3. Vectorized Matcher & 12-Rule Reconciliation Engine

Reconciliation runs in &lt; 1.5s using vectorized `pandas` operations across 2,010 records:

```text
Raw Ingestion → Normalization → Exact ID Joins → Fuzzy Sequence Matching → 12 Financial Rule Checks → IsolationForest ML → Risk Priority Scoring → Database Persistence
```

### The 12 Ground-Truth Financial Rule Checks
1. `MISSING_PAYMENT`: Order paid status in ERP but 0 payment capture record.
2. `PAYMENT_WITHOUT_ORDER`: Gateway capture exists with no corresponding ERP order ID.
3. `DUPLICATE_PAYMENT`: Multiple successful captures for single order ID.
4. `PARTIAL_PAYMENT`: Captured payment amount &lt; ERP order amount.
5. `OVERPAYMENT`: Captured payment amount &gt; ERP order amount.
6. `SETTLEMENT_MISMATCH`: Net bank payout advice variance vs gateway captured minus MDR.
7. `MISSING_SETTLEMENT`: Payment captured &gt; 48 hours ago with 0 bank payout UTR advice.
8. `DELAYED_SETTLEMENT`: Bank payout received 5–12 days past standard T+2 SLA.
9. `DUPLICATE_SETTLEMENT`: Multiple payout advices referencing same UTR or payment ID.
10. `REFUND_MISMATCH`: Refund advice discrepancy vs original gateway capture.
11. `INVOICE_MISMATCH`: Vendor tax invoice amount variance vs ERP order net total.
12. `FEE_ANOMALY`: Gateway MDR charge rate deviating beyond agreed channel threshold.

---

## 4. Machine Learning & Anomaly Detection

In addition to deterministic rules, `apps/api/app/engine/anomaly_detector.py` uses `scikit-learn` `IsolationForest`:
- Feature Vector: `[MDR_Fee_Percentage, Transaction_Amount, Channel_Code, Settlement_Window_Days]`
- Contamination Rate: `0.05`
- Detects non-linear fee overcharges and hidden gateway MDR anomalies.

---

## 5. Grounded AI Copilot & Fallback Engine

The AI Copilot (`POST /api/copilot/query`) enforces strict zero-hallucination safety:
- **Fallback Mode**: Operates 100% reliably without requiring an `OPENAI_API_KEY` using a deterministic grounded rules engine.
- **OpenAI Mode**: If `OPENAI_API_KEY` is present, passes retrieved SQLite database records to `gpt-4o-mini` with zero-hallucination instructions.
- **Evidence Citation**: Cites specific IDs (`EXC_1001`, `ord_live_1001`).
- **Insufficient Evidence**: Returns `"I don't have enough data in the current reconciliation run to answer that."` when queries are out of domain.
- **Human-in-the-Loop**: AI provides evidence explanations only; human officer approval is required for all status updates.
