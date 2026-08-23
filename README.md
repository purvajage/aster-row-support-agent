# Aster & Row Support Agent

A reliable customer-support agent for Aster & Row that combines local knowledge-base retrieval, deterministic workflow routing, conversation context, and a controlled order-lookup tool.

The agent is designed to answer customer questions using the supplied knowledge base, retrieve authoritative information, handle multi-turn conversations, safely look up orders, protect sensitive information, detect conflicting sources, and abstain when the available information is insufficient.

---

## 1. Key Features

- Knowledge-base retrieval using the supplied Aster & Row documents
- Source-grounded responses with source filename and section references
- Current/authoritative policy handling
- Multi-turn conversation context
- Deterministic order routing
- Order lookup using the supplied order dataset
- Safe handling of missing and unknown order IDs
- Protection of sensitive order information
- Source-conflict detection
- Human handoff for uncertain or conflicting cases
- Prompt-injection protection
- Abstention when information is insufficient
- Automated regression tests
- Deterministic evaluation suite

---

## 2. Architecture

```text
                         User Message
                              |
                              v
                        SupportAgent
                              |
                              v
                    Conversation Context
                              |
                              v
                       Workflow Router
                         /          \
                        /            \
                       v              v
               Order Request     Policy Request
                     |                 |
                     v                 v
                Order Lookup      Local Retrieval
                     |                 |
                     v                 v
              Sanitized Result    Safety Checks
                                         |
                           +-------------+-------------+
                           |                           |
                           v                           v
                    Normal Response             Conflict / Abstain
                           |                           |
                           +-------------+-------------+
                                         |
                                         v
                                  Final Response
```

### Main application components

```text
app/
├── agent.py
├── agent_workflow.py
├── config.py
├── conflict_detector.py
├── context_resolver.py
├── conversation.py
├── document_parser.py
├── embeddings.py
├── llm_client.py
├── local_response.py
├── local_retrieval.py
├── models.py
├── order_tool.py
├── prompts.py
└── retrieval.py
```

---

## 3. Knowledge Base

The supplied knowledge base is stored in:

```text
knowledge-base/
```

It contains policies and product information covering areas such as:

- Returns
- Final-sale products
- Damaged or incorrect items
- Domestic shipping
- International shipping
- Warranty
- Order changes and cancellations
- TrailPlus membership
- Gift cards and price adjustments
- Product care
- Breeze Tumbler product information
- Support escalation

The retrieval system preserves source metadata including:

- Source filename
- Section/heading
- Retrieval score

Responses include source references so answers can be traced back to the supplied knowledge base.

---

## 4. Order Data

Order information is stored in:

```text
data/orders.json
```

The project also contains:

```text
data/orders-data-dictionary.md
```

The order lookup tool is responsible for retrieving order information.

Customer-facing responses are sanitized so that internal information such as customer email, address, internal notes, and risk scores are not disclosed.

---

## 5. Conversation Context

Conversation state is maintained using:

```text
app/conversation.py
app/context_resolver.py
```

This allows the agent to resolve follow-up questions using information from previous turns.

Example:

```text
User: Where is ORD-1007?

Agent: Your order ORD-1007 is currently shipped. Carrier: UPS...

User: When will it arrive?

Agent: Your order ORD-1007 is currently shipped. Carrier: UPS...
```

The second question can use the previously established order context without requiring the customer to repeat the order ID.

---

## 6. Safety and Reliability

### Missing Order ID

If a customer asks:

```text
Where is my order?
```

without providing an order ID, the agent asks for the order ID instead of inventing an order status or tracking number.

### Unknown Order

For an unknown order such as:

```text
Please check ORD-9999.
```

the agent reports that the order was not found and hands the case off when appropriate.

### Cancelled Orders

Cancelled orders do not use stale delivery estimates.

### Missing Delivery Estimates

If an order is shipped but the delivery estimate is unavailable, the agent does not invent an arrival date.

### Privacy

The agent does not disclose:

- Customer email
- Customer address
- Internal notes
- Risk scores
- Fraud-review information

### Source Conflicts

When current authoritative sources disagree, the agent does not silently choose one source.

For example, the Breeze Tumbler documentation contains conflicting dishwasher guidance. The agent reports the conflict, recommends human confirmation, and provides safest interim guidance.

### Insufficient Information

When the supplied knowledge base does not contain enough information to answer reliably, the agent abstains and recommends human confirmation.

### Prompt Injection

Untrusted instructions in retrieved documents do not override authoritative policies.

For example, a migration note requesting that the current return policy be ignored does not override the current official returns policy.

---

## 7. Project Structure

```text
aster-row-support-agent/
│
├── app/
│
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
│
├── evaluation/
│   ├── run_evaluation.py
│   └── visible-cases.json
│
├── knowledge-base/
│   └── *.md
│
├── logs/
│
├── scripts/
│
├── tests/
│   ├── test_agent_workflow.py
│   ├── test_context_resolver.py
│   ├── test_conversation.py
│   ├── test_order_tool.py
│   └── test_retrieval.py
│
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## 8. Setup

Create a Python virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies using the repository's dependency configuration.

---

## 9. Environment Variables

Create a local `.env` file using `.env.example` as the template.

Example:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Do not commit API keys or other secrets to Git.

The real `.env` file is excluded through `.gitignore`.

---

## 10. Running the Tests

Run the automated test suite with:

```powershell
pytest -q
```

The tests cover areas including:

- Workflow routing
- Context resolution
- Conversation handling
- Order lookup
- Retrieval

---

## 11. Running the Evaluation

Run the visible evaluation suite with:

```powershell
python evaluation/run_evaluation.py
```

The visible evaluation cases are stored in:

```text
evaluation/visible-cases.json
```

The evaluation covers:

- Retrieval
- Conversation
- Groundedness
- Multi-source grounding
- Privacy
- Prompt security
- Abstention
- Source conflicts
- Order-tool reliability
- Order-tool usage

---

## 12. Evaluation Results

The system was improved iteratively through repeated evaluation and debugging.

Evaluation progress:

```text
Initial baseline: 3/15
Intermediate:     5/15
Intermediate:     8/15
Intermediate:     9/15
Intermediate:    10/15
Intermediate:    11/15
Intermediate:    14/15
Final:            15/15
```

### Final Visible Evaluation

```text
======================================================================
ASTER & ROW SUPPORT AGENT EVALUATION
======================================================================

Overall: 15/15 passed
```

### Final Category Results

```text
abstention                1/1
conversation              1/1
groundedness              2/2
multi-source-grounding    1/1
privacy                   1/1
prompt-security           1/1
retrieval                 2/2
source-conflict           1/1
tool-reliability          3/3
tool-use                  2/2
```

---

## 13. Bug Diary

### Bug 1 — Policy Question Incorrectly Routed to Order Lookup

#### Reproduction

```text
My TrailPlus membership was active when I ordered.
What is my return window?
```

The initial implementation incorrectly asked for an order ID.

#### Root Cause

The routing logic used broad order-related keyword detection. The word "order" caused a policy question to be treated as an order request.

#### Fix

The routing logic was adjusted so policy questions are handled through knowledge-base retrieval rather than order lookup when an actual order operation is not being requested.

#### Regression Test

The TrailPlus return-window evaluation case now passes.

---

### Bug 2 — Canada Multi-Turn Response Did Not Include All Relevant Information

#### Reproduction

```text
User: Do you ship internationally?

User: What about Canada, and how long does it take?
```

The initial response did not consistently include all relevant Canada delivery information.

#### Root Cause

The response generation did not consistently combine the relevant international-shipping passages.

#### Fix

The response now combines the supported-destination and Canada-delivery information.

The response includes:

- Canada is supported
- 5–9 business days after dispatch
- Processing time
- Duties or taxes are not prepaid

#### Regression Test

The Canada multi-turn evaluation case now passes.

---

### Bug 3 — Conflicting Breeze Tumbler Sources

#### Reproduction

```text
Can I put the entire Breeze Tumbler in the dishwasher?
```

Two current official sources contained conflicting guidance.

#### Root Cause

Retrieval returned both sources, but the initial response path did not safely surface the conflict.

#### Fix

A conflict detector was added so conflicting authoritative claims are surfaced instead of silently selecting one source.

The agent now:

1. Identifies the conflict
2. Does not silently choose one source
3. Recommends human confirmation
4. Provides safest interim guidance

#### Regression Test

The `genuine-active-source-conflict` evaluation case now passes.

---

### Additional Reliability Fixes

Other issues addressed during development included:

- Unknown-order response wording
- Missing-order-ID handling
- Stale ETA for cancelled orders
- Order-response generation after successful tool lookup
- Privacy protection for internal order fields
- Insufficient-information abstention
- Prompt-injection handling
- Authoritative-source filtering
- Deterministic evaluation phrase matching

---

## 14. AI Coding Tools Disclosure

AI coding assistance was used during development for:

- Debugging
- Code review
- Explaining implementation details
- Identifying edge cases
- Generating test ideas
- Iterating on evaluation failures
- Improving error handling

The final implementation was tested locally using the project's automated tests and evaluation suite.

---

## 15. Example of an Incorrect AI Suggestion

During development, an overly broad routing implementation could classify the following policy question as an order request:

```text
My TrailPlus membership was active when I ordered.
What is my return window?
```

This could incorrectly produce:

```text
Please provide your order ID.
```

This was incorrect because the user was asking about the TrailPlus policy rather than requesting an order lookup.

The behavior was identified during testing and the routing logic was corrected.

A regression case was then used to verify the fix.

---

## 16. Known Limitations

- The knowledge base is limited to the supplied Aster & Row documents.
- Order information comes from the supplied dataset rather than a live commerce backend.
- The agent cannot perform real-world actions such as issuing refunds or approving returns.
- Conflicting authoritative information requires human confirmation.
- The system does not include production authentication or authorization.
- The project is designed as a support-agent evaluation/demo system rather than a production deployment.
- No production-scale monitoring or infrastructure is included.
- The `scripts/` directory currently does not contain a separate CLI launcher; the agent can be exercised directly through the Python application interface and evaluation commands.

---

## 17. Original Evaluation Cases

The project also includes additional original regression scenarios beyond the supplied visible evaluation cases.

These cases are intended to test:

- Order-ID normalization
- Multi-turn order context
- Final-sale change-of-mind handling
- Privacy protection for internal order information
- Follow-up behavior after an order lookup

> Update this section with the exact filenames and final results after the five original evaluation cases are added.

---

## 18. Demo

A short 2–4 minute demo will demonstrate:

1. A knowledge-base question with source attribution
2. An order lookup
3. A multi-turn follow-up
4. An uncertainty/refusal or human-confirmation case
5. The evaluation suite running with the final result of 15/15 passed

The demo recording will be added to this section before final submission.

---

## 19. Final Verification

Run the automated tests:

```powershell
pytest -q
```

Run the evaluation:

```powershell
python evaluation/run_evaluation.py
```

Expected final visible evaluation:

```text
Overall: 15/15 passed
```

Finally check Git status:

```powershell
git status
```

Make sure no API keys or other secrets are committed.

---

## 20. Final Status

Current visible evaluation status:

```text
15/15 passed
```

Core agent functionality is complete, including retrieval, order lookup, conversation context, privacy protection, prompt-injection handling, abstention, source-conflict handling, and human handoff.

Remaining submission work includes completing the five original evaluation cases and adding the final demo recording.