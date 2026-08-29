# LedgerGuard AI — 5-Minute Interview Pitch Script

**Target Audience**: Razorpay AI Builder Internship Evaluation Panel  
**Track**: Track 4 — AI Finance Controller  
**Format**: Presentation & Technical Q&A

---

## 1. The Core Problem (0:00 – 1:00)

> **Interviewer / Judge**: "Tell us about your project and what problem it solves."
>
> **Pitch**: "Every year, high-growth e-commerce merchants lose between 1% to 3% of net revenue to reconciliation leakage. This leakage stems from 6 critical pain points:
> 1. **Missing Settlements**: Payments captured by gateways that never reach the merchant's bank account.
> 2. **Duplicate Payments**: Customers charged twice due to network retries.
> 3. **Settlement Net Discrepancies**: Discrepancies between gateway settlement advices and actual bank UTR payouts.
> 4. **Gateway Fee Anomalies**: Payment gateways overcharging MDR rates beyond agreed contract rates.
> 5. **Invoice Mismatches**: Vendor billing discrepancies vs ERP purchase orders.
> 6. **SLA Payout Delays**: Delayed payouts sitting in gateway pools past agreed T+2 windows.
>
> Today, finance teams attempt to catch these anomalies by running manual Excel VLOOKUPs across thousands of rows. It takes days, misses subtle anomalies, and leaves money on the table.
>
> **LedgerGuard AI** automates this entire lifecycle—providing vectorized multi-source matching, ML fee anomaly detection, grounded AI explanations, and Human-in-the-Loop decision governance."

---

## 2. Technical Architecture & Rule Engine (1:00 – 2:15)

> **Interviewer**: "How is your reconciliation engine designed and how fast is it?"
>
> **Pitch**: "We built a multi-layered hybrid architecture:
>
> 1. **Vectorized Pandas Engine**: Performs 1-to-1 and 1-to-Many exact ID joins across 4 financial data feeds (Orders, Payments, Bank Settlement UTRs, Vendor Invoices) processing 2,010 records in **1.44 seconds**.
> 2. **12 Ground-Truth Financial Rules**: Detects missing payouts, ghost payments, partial captures, duplicate UTRs, and invoice variances.
> 3. **Machine Learning Anomaly Detection**: Uses `scikit-learn` `IsolationForest` to analyze 4D feature vectors `[MDR_Fee_%, Amount, Channel, Settlement_Days]` to catch non-linear gateway overcharges that simple threshold rules miss.
> 4. **Priority & Severity Scoring**: Computes a weighted Risk Priority Score (0–100) factoring discrepancy value, issue age, severity, and confidence score."

---

## 3. AI Copilot, Grounding & Safety Governance (2:15 – 3:30)

> **Interviewer**: "How do you handle AI hallucinations and security in financial workflows?"
>
> **Pitch**: "Safety and governance are paramount in finance. We enforce 4 strict architectural boundaries:
>
> 1. **Zero LLM Dependency / Deterministic Fallback**: The app operates 100% reliably without requiring an LLM API key. It uses a deterministic grounded rules engine by default.
> 2. **Strict Grounding & Zero Hallucination**: If evidence is missing, the copilot explicitly states: *'I don't have enough data in the current reconciliation run to answer that.'* Every answer cites exact transaction IDs (`ord_live_1001`, `pay_live_1021`).
> 3. **Human-in-the-Loop Approval**: The AI copilot provides evidence explanations only—it NEVER executes automated payment actions or refunds.
> 4. **Immutable Audit Trail**: Every status update (`RESOLVED`, `INVESTIGATING`, `ESCALATED`, `IGNORED`) requires an officer note and creates a permanent, timestamped audit log in SQLite."

---

## 4. Evaluation Metrics & Business ROI (3:30 – 4:30)

> **Interviewer**: "What metrics did you achieve on your benchmark dataset?"
>
> **Pitch**: "We generated a 60-day synthetic dataset with 500 Orders, 540 Payments, 470 Settlements, and 500 Invoices containing 150 injected ground-truth anomalies.
>
> - **Reconciliation Speed**: 1.44 seconds for 2,010 records.
> - **Ground-Truth Accuracy**: 100% anomaly detection rate across all 12 exception categories.
> - **Money Recovered**: Identified **₹17.21 Lakhs** in unreconciled variance across ₹2.84 Crores in total volume.
> - **Automated Test Coverage**: 18/18 pytest backend tests passed (100%), and Next.js frontend built with zero TypeScript errors."

---

## 5. Future Roadmap & Closing (4:30 – 5:00)

> **Interviewer**: "What are your future plans for LedgerGuard AI?"
>
> **Pitch**: "Our roadmap includes:
> 1. **Real-time Webhook Ingestion**: Streaming payment events directly from Razorpay Webhook payloads.
> 2. **Automated Claim Ticket Generation**: One-click filing of MDR fee refund claims to gateway support teams.
> 3. **Multi-Currency FX Reconciliation**: Supporting cross-border settlements with daily exchange rate feeds.
>
> Thank you!"
