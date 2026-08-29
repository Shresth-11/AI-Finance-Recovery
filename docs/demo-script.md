# LedgerGuard AI — 4-to-5 Minute Video Demonstration Script

**Target Duration**: 4:30  
**Presenter**: Finance Controller / Product Architect  
**Visual Mode**: LedgerGuard AI Dashboard (`http://localhost:3000`)

---

## 🎬 Act 1: Introduction & Problem Framing (0:00 – 0:45)

**[Screen: LedgerGuard AI Overview Dashboard — Dark/Light UI Mode]**

> **Presenter**: "Hello! Welcome to **LedgerGuard AI**, an AI-assisted payment reconciliation and finance exception platform built for the Razorpay AI Builder Internship (Track 4: AI Finance Controller).
>
> In modern e-commerce, finance teams face massive reconciliation leakage: missing bank settlements, duplicate gateway charges, delayed payouts, and hidden fee overcharges. Millions of rupees are lost every quarter because traditional tools rely on slow, manual Excel VLOOKUPs.
>
> LedgerGuard AI solves this by ingesting multi-source transaction feeds—Orders, Payments, Bank Settlement UTRs, and Vendor Invoices—and executing a vectorized 12-rule reconciliation engine with machine learning anomaly detection in less than 2 seconds."

---

## ⚡ Act 2: Ingestion & Reconciliation Execution (0:45 – 1:30)

**[Screen: Navigate to Reconciliation Workspace (`/reconciliation`)]**

> **Presenter**: "Let's look at our **Reconciliation Workspace**.
>
> Step 1: With one click on **'Load Demo Data'**, we seed 2,010 synthetic Indian e-commerce financial records spanning 60 days—500 Orders, 540 Gateway Captures, 470 Bank Settlements, and 500 Invoices.
>
> Step 2: Now I click **'Run Reconciliation'**. Watch the animated progress bar. In just **1.44 seconds**, our vectorized Pandas matcher and scikit-learn IsolationForest ML model process all 2,010 records across 12 financial rule categories.
>
> Notice our run summary: **54.6% cleanly matched**, **227 exceptions detected**, representing **₹17,21,893.36 in money at risk**—achieving **100% ground-truth anomaly detection accuracy**."

---

## 📊 Act 3: Executive Dashboard & Risk Center (1:30 – 2:30)

**[Screen: Navigate to Overview Dashboard (`/`)]**

> **Presenter**: "Returning to our **Financial Operations Overview**, we see high-density financial metrics built with Stripe-like clarity and Ramp-like financial confidence.
>
> Notice our dynamic **Financial Risk Index: CRITICAL RISK (74.5 / 100)** badge.
>
> Look at our 6 KPI Cards:
> 1. Total Processed Volume: **₹2,84,50,000**
> 2. Reconciliation Rate: **54.60%**
> 3. Open Exceptions: **227 Cases**
> 4. Money at Risk: **₹17,21,893.36**
> 5. Critical / High Issues: **35 Urgent Items**
> 6. Settlement Delay: **2.4 Days average vs T+2 SLA Limit**
>
> Below, our interactive **Discrepancy Trend Chart** offers 7d, 30d, and 60d timeframe toggles with full WCAG screen-reader fallbacks."

---

## 🔍 Act 4: Exceptions Triage & Side-by-Side Evidence (2:30 – 3:30)

**[Screen: Navigate to Exceptions Explorer (`/exceptions`) and click row `EXC_1001`]**

> **Presenter**: "Now let's dive into the **Exceptions Explorer**, our primary operational screen.
>
> Using our debounced search bar, I type `EXC_1001` or filter by `CRITICAL` severity. Notice the sticky header counter showing **₹17.21 Lakhs filtered discrepancy**.
>
> Clicking `EXC_1001` opens our **Incident Investigation Workspace**.
>
> Look at our **Side-by-Side Comparison Matrix**:
> - Order `ord_live_1001` was placed for ₹1,500.
> - But Gateway Captures show TWO successful payments (`pay_live_1001` & `pay_live_1021`) for the exact same order!
>
> Look at our **Reconciliation Lifecycle Flow**: Order Created → Payment Captured → Settlement Expected → Exception Flagged.
>
> I enter my resolution note: *'Customer double charged on checkout. Issuing refund via gateway API.'* and click **'Approve & Resolve'**.
>
> Notice the modal confirmation dialog, and watch the **Audit Trail** update instantly with our logged action!"

---

## 🤖 Act 5: Grounded AI Copilot & Reports (3:30 – 4:15)

**[Screen: Navigate to AI Copilot (`/copilot`)]**

> **Presenter**: "Next, let's open our **AI Finance Controller Copilot**.
>
> LedgerGuard AI features a zero-hallucination grounded copilot that operates 100% reliably without requiring an LLM API key using our deterministic fallback engine.
>
> I click the starter query: *'Show the highest-value unresolved issues.'*
>
> Instantly, Copilot analyzes SQLite records and returns our top 5 critical items, citing exact IDs (`EXC_1001`, `EXC_1002`). Every response includes a **Clickable Cited Evidence Badge**, a **One-Click Copy Action**, and a mandatory disclaimer: *'AI-assisted analysis based on synthetic data. Human review is required.'*
>
> Finally, navigating to **Reports (`/reports`)**, we can export filtered CSV audit reports with one click."

---

## 🎯 Act 6: Closing Summary (4:15 – 4:30)

**[Screen: Overview Dashboard (`/`)]**

> **Presenter**: "LedgerGuard AI brings financial confidence, zero-leakage reconciliation, and Human-in-the-Loop AI governance to finance teams. All code, database schemas, and unit tests are 100% verified. Thank you!"
