# Beaver's Choice Paper Company — Multi-Agent System Report

**Framework:** smolagents 1.26 · **Model:** `gpt-4.1-mini` (Vocareum OpenAI-compatible proxy) · **Agents:** 5
**Files:** `project_starter.py` (implementation), `agent_workflow_diagram.png` (diagram), `test_results.csv` (evaluation), `business_advisor_report.md`, `run_log.txt`

---

## 1. System overview and the workflow diagram

The system answers a customer's text request for paper supplies with one complete reply. The reply covers what can be supplied, at what price and with which discount, when it will arrive, and why any item cannot be supplied. The request is then fulfilled: stock is replenished from the supplier where needed and the sale is recorded in the SQLite database.

### 1.1 Agents and responsibilities

| # | Agent | Type | Responsibility (no overlap) |
|---|---|---|---|
| 1 | **Orchestrator Agent** | `OrchestratorAgent` (uses the smolagents model) | Customer-facing coordinator. Reads the request date and the requested delivery date, opens a **case file**, delegates to the workers in a fixed order, and writes the customer reply from verified facts. It never touches the database. |
| 2 | **Inventory Agent** | smolagents `ToolCallingAgent` | Everything about *goods*: maps the customer's wording to exact catalog items (e.g. "500 reams of printer paper" → 250,000 × *Standard copy paper*), checks stock and supplier lead times against the deadline, decides reorder quantities, and places `stock_orders`. |
| 3 | **Quoting Agent** | smolagents `ToolCallingAgent` | Everything about *price*: benchmarks against historical quotes, prices only the lines that can be delivered on time, applies the bulk-discount tier, and explains the pricing. |
| 4 | **Sales Agent** | smolagents `ToolCallingAgent` | Everything about *closing the order*: re-verifies stock, records one `sales` transaction per line at the discounted price, and issues the order number. |
| 5 | **Business Advisor Agent** | smolagents `ToolCallingAgent` | Internal only (stand-out feature). After the batch, analyses the financial report and sales activity and recommends assortment, pricing and stock-policy changes (`business_advisor_report.md`). |

### 1.2 Flow for every request (numbers match the diagram)

1. **Orchestrator → Inventory Agent (ASSESS).** The agent calls `list_catalog_with_stock`, maps each requested line to a catalog item (or `null` if we do not carry it), then calls `assess_order_availability` once. Each line gets one of three statuses:
   - `AVAILABLE_FROM_STOCK`: ships the next day.
   - `RESTOCK_REQUIRED`: the supplier ETA for *shortfall + minimum-stock buffer* still meets the deadline, and cash stays above a $2,000 reserve.
   - `UNAVAILABLE`: comes with a reason (not carried / paper size not stocked / deadline cannot be met).
2. **Orchestrator → Quoting Agent (QUOTE).** This step is skipped when no line can be supplied. The agent calls `find_similar_past_quotes`, then `create_quote`, which prices the deliverable lines at list price and applies the tier discount. The discount depends on the order's total units: 500+ → 5%, 1,000+ → 10%, 5,000+ → 12%, 10,000+ → 15%. Large totals are rounded down to whole dollars, as in the historical quotes.
3. **Orchestrator → Inventory Agent (PREPARE STOCK).** `prepare_stock_for_quote` places supplier orders for any shortfall, again re-checking the cash reserve.
4. **Orchestrator → Sales Agent (FINALIZE).** `finalize_sale` re-verifies stock line by line and writes the `sales` transactions.
5. **Orchestrator → Customer.** The LLM writes the reply using only the facts in the case file. It is told never to reveal cash, costs, margins, stock counts, internal ids, tool names or errors.

### 1.3 Tools and the starter helper functions they use

| Agent | Tool | Purpose | Starter helpers used |
|---|---|---|---|
| Inventory | `list_catalog_with_stock` | Catalog + prices + stock for item mapping | `get_all_inventory` |
| Inventory | `check_item_stock` | Stock of one item and its minimum level | `get_stock_level` |
| Inventory | `check_supplier_delivery` | Supplier ETA for a quantity | `get_supplier_delivery_date` |
| Inventory | `assess_order_availability` | Per-line feasibility vs. deadline; saves the assessment | `get_stock_level`, `get_supplier_delivery_date`, `get_cash_balance` |
| Inventory | `prepare_stock_for_quote` | Places restock orders (shortfall + buffer) | `create_transaction` (`stock_orders`), `get_stock_level`, `get_cash_balance`, `get_supplier_delivery_date` |
| Inventory / Advisor | `review_reorder_needs` | Lists stocked items below their minimum level | `get_all_inventory`, `get_supplier_delivery_date` |
| Quoting | `find_similar_past_quotes` | Historical quotes for benchmarking | `search_quote_history` |
| Quoting | `create_quote` | Prices deliverable lines, applies the discount tier | (case-file assessment) |
| Sales | `get_quote_details` | Reads the current quote | (case file) |
| Sales | `finalize_sale` | Records the sale, returns the order number | `create_transaction` (`sales`), `get_stock_level`, `get_cash_balance` |
| Advisor | `get_financial_report` | Cash, inventory value, low stock, top sellers | `generate_financial_report` |
| Advisor | `get_sales_activity_summary` | Quotes, orders, revenue, decline reasons | (case-file registries) |

All seven required helpers are used: `create_transaction`, `get_all_inventory`, `get_stock_level`, `get_supplier_delivery_date`, `get_cash_balance`, `generate_financial_report` and `search_quote_history`. `init_database` and `generate_sample_inventory` are used by the test harness.

### 1.4 Why this architecture — decisions made along the way

- **Separating responsibilities by business domain (goods / price / closing).** Each piece of business data has exactly one owner. Only the Inventory Agent writes `stock_orders` and only the Sales Agent writes `sales`, which keeps the agents' responsibilities from overlapping and makes failures easy to trace.
- **LLM for language, deterministic tools for money.** The LLM is good at the hard, fuzzy part: mapping "heavy cardstock (white)" to *Cardstock*, or "500 reams" to 250,000 sheets. It is unreliable at arithmetic and bookkeeping. So every price, discount, stock check, date comparison and transaction happens inside a tool, and the LLM decides which tool to call and explains the outcome.
- **A shared case file (blackboard) instead of passing ids.** My first version passed reference ids (`ASM-…`, `Q-…`) between agents through the LLM. Testing showed smolagents' managed-agent answer template dropped the id, and the orchestrator then invented one (`ASM-xxxx`, even a tool-call id). That produced a quote built from a different customer's request. Saving the assessment and quote to the active case file removed this whole class of errors.
- **An orchestrator with an explicit delegation order.** I first used a free-form LLM manager (smolagents `managed_agents`). In testing it ran steps in parallel (which corrupted a transaction id), repeated assessments, used wrong request dates, and sometimes asked the customer to "confirm" instead of finalizing. Because steps 3–4 move money, the orchestrator now follows a fixed, auditable order. Guardrails re-run a step's tool directly if a worker finishes without doing it; none of them fired in the final run. The orchestrator still uses the LLM for the customer reply.
- **Deterministic guardrails for item mapping.** Sizes we do not stock (A3/A5) and products we never carry (balloons, tickets, cardboard) are declined by code, based on the customer's wording. This was added after an earlier run sold "A5 colored paper" as standard *Colored paper*.
- **Cost model.** Supplier cost is set to 60% of list price (`SUPPLIER_COST_RATIO`), so restocking to fill an order is profitable even after discounts. The margin stays inside the tools and never reaches customers.

---

## 2. Evaluation results (`test_results.csv`)

All 20 requests in `quote_requests_sample.csv` were processed in date order. The full console trace is in `run_log.txt`.

| Metric | Result | Requirement |
|---|---|---|
| Requests that changed the cash balance | **15** | ≥ 3 ✅ |
| Requests fulfilled (fully or partially, with an order number) | **15** (6 in full, 9 partially) | ≥ 3 ✅ |
| Requests left completely unfulfilled, with a reason | **5** (#9, #13, #15, #16, #18) | ≥ 1 ✅ |
| Cash balance | $45,059.70 → **$49,017.33** | |
| Inventory value | $4,940.30 → $4,363.90 | |
| Total assets | $50,000.00 → **$53,381.23 (+6.8%)** | |
| Revenue / discounts granted | $11,860.90 / $1,885.48 | |
| Guardrail fallbacks triggered | 0 | |
| Replies containing internal data (ids, stock counts, cash, errors) | 0 (automated scan) | |

### Per-request outcomes

| Req | Date | Outcome | Total | Unfulfilled lines and reason given |
|---|---|---|---|---|
| 1 | 04-01 | Full | $65.00 | — |
| 2 | 04-03 | Partial | $133.00 (5%) | balloons: not carried |
| 3 | 04-04 | Partial | $8,925.00 (15%) | A3 paper: size not stocked |
| 4 | 04-05 | Full | $83.00 (5%) | — |
| 5 | 04-05 | Full | $121.00 (10%) | — |
| 6 | 04-06 | Full | $85.00 (10%) | — |
| 7 | 04-07 | Partial | $387.00 (10%) | A3 matte: size not stocked |
| 8 | 04-07 | Partial | $468.00 (10%) | A5 colored: size not stocked |
| 9 | 04-07 | **Declined** | — | A4: earliest delivery Apr 11 > Apr 10 deadline; A3 glossy; kraft envelopes |
| 10 | 04-08 | Full | $137.00 (5%) | — |
| 11 | 04-08 | Partial | $54.00 | A3 glossy: size not stocked |
| 12 | 04-08 | Full | $49.40 (5%) | — |
| 13 | 04-08 | **Declined** | — | A4 + cardstock: restock cannot arrive by Apr 10 |
| 14 | 04-09 | Partial | $71.00 (5%) | A4 + poster paper: restock after Apr 15 deadline |
| 15 | 04-12 | **Declined** | — | 10,000 A4: earliest Apr 19; A3 colored; cardboard not carried |
| 16 | 04-13 | **Declined** | — | A4 + colored paper: deadline; poster board not carried |
| 17 | 04-14 | Partial | $47.50 (5%) | A4, napkins, cups: deadline; A3 colored: size |
| 18 | 04-14 | **Declined** | — | all lines need a 4-day restock, deadline is the next day |
| 19 | 04-15 | Partial | $135.00 (10%) | glossy: deadline; A3 matte: size |
| 20 | 04-17 | Partial | $1,100.00 (12%) | tickets: not carried |

### Strengths shown by the results

1. **It sells as much as possible and declines only what it must.** 15 of 20 customers got an order. When only part of a request could be met, the system fulfilled what it could and explained each remaining line, rather than rejecting the whole order (e.g. #3, #20).
2. **It checks deadlines correctly with the supplier's lead-time rules.** Declines come from real constraints. For example, #9 needs 200 sheets of A4 by Apr 10, warehouse stock is too low, and a restock placed on Apr 7 arrives Apr 11. Late-month requests (#13–#18) are declined more often as deadlines get shorter, which is the behavior we want.
3. **Restocking is just-in-time and profitable.** Shortfalls are bought with a buffer back to the minimum stock level, so no stocked item ended the run below its minimum. Cash rose on every fulfilled request, and total assets grew 6.8%.
4. **Pricing is transparent and consistent.** Every reply lists the unit price, line totals, subtotal, discount tier with its rule ("10% bulk discount for orders of 1,000+ units") and the total. The courtesy rounding matches the style of the historical quotes.
5. **Customer replies are safe and explain their reasons.** Each decline carries a plain-language reason and an offer of alternatives. An automated scan found no internal ids, stock counts, cash figures or error messages in any reply.
6. **Data stays consistent.** Every transaction is dated with the request date, so `generate_financial_report(request_date)` in the harness reflects each order immediately.

### Weaknesses observed

- **Item mapping still varies with the LLM.** "Colorful cardstock" was mapped to *Cardstock* in this run but to *Colored paper* in an earlier one. "100% recycled kraft paper envelopes" (#9) was treated as not carried, even though *Envelopes* is in the catalog. "Poster boards" became *Large poster paper* in #7 but were declined in #16.
- **No partial-quantity or split-delivery offers.** If 500 sheets are needed and only 135 are in stock, the whole line is declined. The system does not offer to ship 135 now and the rest later.
- **Same-day restocks are booked on the request date.** This keeps the ledger simple, but goods "in transit" count as stock immediately.

---

## 3. Suggestions for further improvement

1. **Deterministic item matching backed by an LLM.** Replace free-form mapping with a matcher based on a synonym table or embeddings (e.g. "printer paper" ↔ *Standard copy paper*, "kraft envelopes" ↔ *Envelopes*), ask the LLM only when confidence is low, and log every mapping for review. This would fix the inconsistencies above and lower token use.
2. **Partial shipments, back-orders and alternative offers.** When a deadline cannot be met, offer (a) the in-stock quantity now and the remainder on the supplier ETA, or (b) the closest product we carry (e.g. A4 instead of A3). A **customer negotiation agent** could accept or counter these offers using the job/event context in the request data.
3. **Margin-aware and history-driven pricing.** Learn discount tiers from `quotes.csv` (average discount by order size and event type). Add a minimum-margin rule so discounts never push a line below cost. Let the Business Advisor tune `BULK_DISCOUNT_TIERS` based on win rate and revenue.
4. **Proactive replenishment and supplier-aware reorder points.** Run `review_reorder_needs` on a schedule and set reorder points from demand velocity × supplier lead time, instead of a static `min_stock_level`. This would have turned several late-month deadline declines (#13–#18) into sales.
5. **Persistent case files and observability.** Store case files and agent traces in the database (not in memory) so runs can be resumed and audited. Report latency, token cost and guardrail activations for each request.

---

## 4. Stand-out features implemented

- **Business Advisor Agent:** analyses all transactions after the batch and recommends changes (see `business_advisor_report.md`). Its top recommendation is to expand the assortment to A3/A5 sizes, which was the most common reason for declined lines.
- **Live terminal trace:** each step prints a progress line (`[Orchestrator] -> inventory_agent …`, `[Inventory Agent] Restocked …`, `[Sales Agent] Order SO-… recorded`) so you can follow a request through the system as it runs.
