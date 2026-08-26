# Aster & Row Support Agent

A reliable customer-support agent for Aster & Row, a fictional ecommerce company selling bags, drinkware, and travel accessories.

The system combines local knowledge-base retrieval, deterministic workflow routing, multi-turn conversation context, a controlled order-lookup tool, source-conflict detection, privacy safeguards, prompt-injection handling, and safe abstention.

The implementation is intentionally small and focused on reliability rather than a large production stack.

---

## 1. Assignment Goal

The project was built for the **AI Agent Intern Take-Home: Build a Reliable RAG Support Agent** assignment.

The main reliability problems addressed are:

1. Conflicting policy answers.
2. Invented order information.
3. Lost conversation context.
4. Unsafe instructions contained inside retrieved documents.

The agent is designed to use the supplied company content as the source of truth, safely access mock order data only when required, preserve relevant conversation context, and recommend human assistance when information is insufficient or authoritative sources conflict.

---

## 2. Key Features

- Knowledge-base retrieval over the supplied Markdown documents.
- Document parsing with useful source metadata.
- Local retrieval instead of sending the entire knowledge base to the model.
- Source-grounded policy and product answers.
- Filename and relevant heading included in policy/product citations.
- Preference for current/authoritative policy content.
- Handling of superseded/legacy content.
- Multi-turn conversation context.
- Deterministic workflow routing.
- Controlled order lookup using `data/orders.json`.
- Order-ID normalization, including harmless lowercase/whitespace differences.
- Safe handling of missing, malformed, and unknown order IDs.
- Current order status treated as authoritative.
- No invented delivery estimates.
- No stale ETA shown for cancelled/returned orders.
- Customer/internal-data privacy protection.
- Prompt-injection protection for retrieved content.
- Detection of genuine active-source conflicts.
- Safe abstention when the knowledge base is insufficient.
- Human-handoff flags for uncertain or unsupported cases.
- Deterministic evaluation assertions.
- Original regression cases in addition to the supplied visible cases.
- Debug/trace information for development and troubleshooting.

---

## 3. Architecture

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
                       /              \
                      /                \
                     v                  v
              Order Request       Knowledge Request
                    |                    |
                    v                    v
              Order Lookup        Local Retrieval
                    |                    |
                    v                    v
             Sanitized Result     Safety / Source Checks
                                         |
                              +----------+----------+
                              |                     |
                              v                     v
                       Normal Response       Conflict / Abstain
                              |                     |
                              +----------+----------+
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

### Design approach

The application uses a **custom Python workflow** rather than a large agent framework. Routing is intentionally deterministic for important safety-sensitive decisions such as order lookup, prompt-injection refusal, source conflicts, and abstention.

The model is used where generation is useful, while deterministic application logic controls the high-risk paths.

---

## 4. Tech Stack

| Area | Choice |
|---|---|
| Language | Python |
| Agent/workflow | Custom Python workflow |
| LLM | OpenAI API |
| Default model | `gpt-5-mini` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Retrieval | Local retrieval/index over the supplied Markdown corpus |
| Source format | Markdown with document metadata/front matter |
| Order data | JSON |
| Tests | pytest |
| Evaluation | Deterministic Python evaluation suite |
| Interface | Python application/CLI-style commands |
| Storage | Local files and local retrieval/index structures |

The project does not require a production vector database, deployment platform, fine-tuning, or a polished frontend.

---

## 5. Knowledge Base / RAG

The supplied knowledge base is stored in:

```text
knowledge-base/
```

It contains information covering:

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
- Internal/migration content

The retrieval pipeline parses and indexes the supplied documents rather than placing the entire corpus into the model prompt.

Useful metadata is retained, including:

- Source filename
- Section/heading
- Retrieval score
- Document metadata where available

Policy/product answers include source references such as:

```text
Source: 01-returns-policy-current.md — Standard return window
```

### Source precedence

The application deliberately distinguishes current authoritative content from superseded or instruction-like content.

For example, an internal migration note cannot override the current returns policy.

### Active source conflicts

If two current authoritative sources genuinely disagree, the agent does not silently select one.

For example, the Breeze Tumbler documentation contains conflicting dishwasher guidance. The agent surfaces the conflict, recommends human confirmation, and provides safe interim guidance.

---

## 6. Order Lookup Tool

Order data is stored in:

```text
data/orders.json
```

The data dictionary is:

```text
data/orders-data-dictionary.md
```

The order lookup is implemented as a controlled application function.

The model does **not** receive the entire orders dataset. The workflow performs a lookup only when order information is actually required.

### Order behavior

The agent:

- Requests an order ID when one is missing.
- Normalizes harmless input differences such as lowercase IDs.
- Handles unknown order IDs safely.
- Handles malformed IDs without inventing information.
- Uses the order's current `status` as authoritative.
- Avoids inventing delivery estimates.
- Avoids stale ETA information for cancelled/returned orders.
- Reports a real lookup failure when an order is not found.
- Does not claim a lookup occurred when it did not.

### Privacy

Customer-facing responses do not expose:

- Customer email
- Customer address
- Internal notes
- Risk scores
- Fraud-review information
- Other internal-only fields

The assignment explicitly treats possession of the order ID as sufficient authentication for this mock system.

---

## 7. Multi-Turn Conversation

Conversation state is maintained using:

```text
app/conversation.py
app/context_resolver.py
```

The agent keeps relevant session context and uses it for short follow-up questions.

Example:

```text
User: Where is ORD-1007?

Agent: Your order ORD-1007 is currently shipped. Carrier: UPS.
       Tracking number: 1ZAR100700000007.
       Estimated delivery: August 22, 2026.

User: When will it arrive?

Agent: Your order ORD-1007 is currently shipped. Carrier: UPS.
       Tracking number: 1ZAR100700000007.
       Estimated delivery: August 22, 2026.
```

The second question does not require the customer to repeat the order ID.

The same mechanism handles policy follow-ups such as:

```text
User: Do you ship internationally?

User: What about Canada, and how long does it take?
```

Session state is isolated by session ID so unrelated conversations are not mixed.

---

## 8. Safety and Reliability

### Missing order ID

For:

```text
Where is my order?
```

the agent asks for the order ID rather than inventing an order status or tracking number.

### Unknown order

For:

```text
Please check ORD-9999.
```

the agent performs the lookup and safely reports that the order was not found, with human handoff when appropriate.

### Cancelled order

Cancelled orders use the current cancellation status and do not reuse stale delivery information.

### Missing ETA

If an order is shipped but no reliable delivery estimate is available, the agent does not invent an arrival date.

### Privacy

Internal order fields are never intentionally exposed in customer-facing responses.

### Insufficient information

When the supplied knowledge base does not contain enough information to answer reliably, the agent abstains and recommends human confirmation.

Example:

```text
The supplied information is insufficient to answer that reliably.
I cannot confirm a material certification or vegan guarantee
from the available knowledge base. Human confirmation is recommended.
```

### Prompt injection

Retrieved documents are treated as untrusted data.

For example, a migration note requesting that the current returns policy be ignored does not override the current official policy.

The agent responds using the authoritative policy and does not automatically approve a return.

### Source conflict

When current authoritative sources conflict, the agent explicitly reports the conflict rather than pretending that one source is definitely correct.

---

## 9. Project Structure

```text
aster-row-support-agent/
│
├── app/
│   ├── agent.py
│   ├── agent_workflow.py
│   ├── config.py
│   ├── conflict_detector.py
│   ├── context_resolver.py
│   ├── conversation.py
│   ├── document_parser.py
│   ├── embeddings.py
│   ├── llm_client.py
│   ├── local_response.py
│   ├── local_retrieval.py
│   ├── models.py
│   ├── order_tool.py
│   ├── prompts.py
│   └── retrieval.py
│
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
│
├── evaluation/
│   ├── run_evaluation.py
│   ├── visible-cases.json
│   └── original-cases.json
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
├── .env.example
├── .gitignore
└── README.md
```

---

## 10. Setup

### 10.1 Clone the repository

```powershell
git clone https://github.com/purvajage/aster-row-support-agent
cd aster-row-support-agent
```

### 10.2 Create a virtual environment

```powershell
python -m venv .venv
```

### 10.3 Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 10.4 Install dependencies

Install the dependencies defined by the repository's dependency configuration.

If the project uses a `requirements.txt`:

```powershell
pip install -r requirements.txt
```

---

## 11. Environment Variables

Create a local `.env` file using `.env.example` as the template.

Example:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Never commit the real API key.

The real `.env` file is excluded by `.gitignore`.

A safe `.env.example` should contain placeholders only:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## 12. Running Tests

Run the automated unit/regression tests:

```powershell
pytest -q
```

The tests cover areas including:

- Workflow routing
- Context resolution
- Conversation handling
- Order lookup
- Retrieval
- Safety-sensitive workflow behavior

---

## 13. Running the Evaluation

Run the complete evaluation suite with:

```powershell
python evaluation/run_evaluation.py
```

The visible cases are stored in:

```text
evaluation/visible-cases.json
```

The five additional original regression cases are stored in:

```text
evaluation/original-cases.json
```

The evaluation suite reports individual case results and category-level results.

It checks behavior including:

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

The suite uses deterministic assertions wherever practical rather than relying exclusively on another LLM to grade the agent.

---

## 14. Evaluation Results

The system was developed iteratively by running the evaluation suite, investigating failures, and adding regression coverage.

### Development progression

The visible evaluation initially scored:

```text
3/15 passed
```

During development, intermediate results included:

```text
5/15
8/15
9/15
10/15
11/15
14/15
15/15
```

After adding five original regression cases, the expanded suite initially reached:

```text
17/20
```

Further conversation-context fixes brought the final result to:

```text
20/20
```

### Final result

```text
======================================================================
ASTER & ROW SUPPORT AGENT EVALUATION
======================================================================

Overall: 20/20 passed
```

### Final category results

```text
abstention                1/1
conversation              3/3
groundedness              3/3
multi-source-grounding    1/1
privacy                   2/2
prompt-security           1/1
retrieval                 2/2
source-conflict           1/1
tool-reliability          3/3
tool-use                  3/3
```

### Final visible and original cases

The final suite contains:

- 15 supplied visible cases
- 5 original regression cases
- **20 total cases**
- **20/20 passed**

Original cases cover:

```text
original-lowercase-order-id
original-order-followup-context
original-final-sale-change-of-mind
original-internal-risk-score
original-cancelled-order-followup
```

---

## 15. Bug Diary

The following failures were reproduced during development and fixed with regression coverage.

### Bug 1 — Policy question incorrectly routed to order lookup

#### Reproduction

```text
User:
My TrailPlus membership was active when I ordered.
What is my return window?
```

#### Observed failure

The initial implementation could interpret the word `order` as an order-status request and ask the customer for an order ID.

#### Root cause

Broad order-related keyword detection was evaluated before the more specific policy intent.

#### Fix

The workflow was changed so policy questions such as TrailPlus return-window questions are routed through knowledge-base retrieval rather than order lookup.

#### Regression coverage

```text
trailplus-return-window
```

Result:

```text
PASS
```

---

### Bug 2 — Canada multi-turn answer was incomplete

#### Reproduction

```text
User: Do you ship internationally?
User: What about Canada, and how long does it take?
```

#### Observed failure

The initial implementation did not consistently include all relevant Canada delivery details.

#### Root cause

Retrieval and response generation did not reliably combine the supported-destination and Canada-delivery passages.

#### Fix

The international-shipping retrieval path was made more targeted and the response includes the relevant information:

- Canada is supported.
- Typical delivery is 5–9 business days after dispatch.
- Processing time is usually 1–2 business days.
- Duties or taxes are not prepaid.

#### Regression coverage

```text
canada-multiturn
```

Result:

```text
PASS
```

---

### Bug 3 — Genuine active source conflict was silently resolved

#### Reproduction

```text
Can I put the entire Breeze Tumbler in the dishwasher?
```

#### Observed failure

Two current official sources contained conflicting dishwasher guidance.

#### Root cause

Retrieval returned both sources, but the initial response path did not explicitly detect and surface the contradiction.

#### Fix

A source-conflict detector was added.

The agent now:

1. Detects conflicting authoritative claims.
2. Does not silently choose one source.
3. Recommends human confirmation.
4. Provides safest interim guidance.

#### Regression coverage

```text
genuine-active-source-conflict
```

Result:

```text
PASS
```

---

### Bug 4 — Order follow-up lost conversation context

This was discovered during testing of the original regression cases rather than only from the initial visible cases.

#### Reproduction

```text
User: Where is ORD-1007?

Agent:
Your order ORD-1007 is currently shipped...
Estimated delivery: August 22, 2026.

User: When will it arrive?
```

#### Observed failure

The follow-up was initially routed to the insufficient-information path and resulted in a human handoff.

#### Root cause

The session contained the active order ID, but the workflow did not route recognized short order follow-ups back through the order lookup path.

#### Fix

The context resolver and workflow now retain the active order ID and perform another controlled order lookup for recognized follow-up questions.

#### Regression coverage

```text
original-order-followup-context
```

Result:

```text
PASS
```

---

### Bug 5 — Cancelled-order follow-up lost context

#### Reproduction

```text
User: What happened to ORD-1004?

Agent:
The order is cancelled and it will not be shipped.

User: So when will it arrive?
```

#### Observed failure

The follow-up was initially treated as insufficient information.

#### Root cause

The follow-up contained no explicit order ID even though the session already had the cancelled order.

#### Fix

The active session order is now reused for recognized follow-up questions.

The current order status remains authoritative, so the response does not invent an arrival date for a cancelled order.

#### Regression coverage

```text
original-cancelled-order-followup
```

Result:

```text
PASS
```

---

### Additional fixes

Other issues addressed during development included:

- Unknown-order response wording.
- Missing-order-ID behavior.
- Lowercase order-ID normalization.
- Stale ETA handling for cancelled/returned orders.
- Successful order-response generation.
- Privacy protection for internal order fields.
- Insufficient-information abstention.
- Prompt-injection handling.
- Authoritative-source filtering.
- Final-sale change-of-mind handling.
- Deterministic evaluation phrase matching.

---

## 16. Observability / Debug Mode

The application provides development-time information that makes workflow decisions inspectable.

Useful debug fields include:

- Current user message.
- Session/conversation context.
- Selected workflow action.
- Retrieved source filenames.
- Retrieved headings.
- Retrieval information/scores where available.
- Whether an order tool was called.
- Sanitized tool results.
- Final answer.
- Human-handoff status.
- Errors/fallback behavior.

Example diagnostic output:

```text
ANSWER: ...
ACTION: order_lookup
HANDOFF: False
TOOL: True
SOURCES: [...]
```

Sensitive information is not intentionally exposed through customer-facing responses.

Secrets such as API keys must never be logged.

---

## 17. AI Coding Tools Used

AI coding assistance was used during development, primarily with ChatGPT.

It was used for:

- Debugging Python errors.
- Reviewing workflow logic.
- Explaining implementation details.
- Identifying edge cases.
- Generating test ideas.
- Interpreting evaluation failures.
- Improving error handling.
- Reviewing README/documentation structure.

The AI suggestions were treated as suggestions rather than automatically trusted changes. Changes were verified locally using Python compilation, targeted diagnostics, automated tests, and the full evaluation suite.

---

## 18. Example of an Incorrect or Incomplete AI Suggestion

One intermediate AI-assisted change introduced an `_handle_order_lookup()` call before the helper existed.

This caused:

```text
NameError: name '_handle_order_lookup' is not defined
```

Another intermediate workflow edit caused an indentation/return-path problem that eventually resulted in:

```text
AttributeError: 'NoneType' object has no attribute 'action'
```

These failures demonstrated why generated code was not accepted blindly.

The issues were caught through local execution and the evaluation suite, corrected, and re-tested until the complete evaluation reached:

```text
20/20 passed
```

A separate routing issue was also identified where broad order keyword matching could confuse a policy question containing the word `order` with an actual order lookup request. That was fixed by making routing more intent-specific.

---

## 19. Known Limitations

- The knowledge base is limited to the supplied Aster & Row documents.
- Order information comes from the supplied mock JSON dataset rather than a live commerce backend.
- Possession of an order ID is treated as sufficient authentication, as required by the assignment.
- The agent can look up orders but does not perform real refunds, cancellations, replacements, or address changes.
- Human handoff is represented by a workflow flag rather than a live ticketing/support integration.
- Conflicting authoritative sources require human confirmation.
- The retrieval implementation is intentionally local and lightweight rather than production-scale.
- The system does not include production authentication or authorization.
- The current interface is intended for demonstration/evaluation rather than production deployment.
- Production deployment would require stronger secret management, authentication, rate limiting, monitoring, alerting, and integration with real commerce systems.
- The `scripts/` directory is currently empty; the documented evaluation and application commands are run directly through Python.

---

## 20. What I Would Improve Before Production

If this were being taken beyond the take-home assignment, I would prioritize:

1. Connect the order tool to a real order-service API.
2. Add authentication and authorization.
3. Add structured production tracing and metrics.
4. Add retrieval-quality monitoring and offline retrieval benchmarks.
5. Add a production vector store if corpus size required it.
6. Add stronger source-version/precedence management.
7. Add automated regression execution in CI.
8. Add rate limiting and abuse protection.
9. Add human-support ticket integration.
10. Add monitoring and alerting for tool failures and source conflicts.
11. Add broader adversarial prompt-injection testing.
12. Add evaluation coverage for paraphrases and unseen combinations.

The current implementation intentionally avoids these production-scale components because the assignment prioritizes a small, reliable system within the 6–8 hour timebox.

---

## 21. Demo

A 2–4 minute demo should demonstrate the following:

### 1. Knowledge-base question

Show a policy question and the returned source citation.

Example:

```text
What is the standard return window?
```

The response should include the relevant policy source.

### 2. Order lookup

Show:

```text
Where is ORD-1007?
```

and demonstrate that the response comes from an actual order lookup.

### 3. Multi-turn conversation

Show:

```text
Do you ship internationally?

What about Canada, and how long does it take?
```

### 4. Safe abstention / human assistance

Show:

```text
Are all fabrics and adhesives in your bags vegan?
```

and demonstrate that the agent does not invent a certification and recommends human confirmation.

### 5. Evaluation

Run:

```powershell
python evaluation/run_evaluation.py
```

and show:

```text
Overall: 20/20 passed
```

### Demo media

Add the final 2–4 minute GIF or video here before submission.

Example Markdown for a GIF:

```markdown
![Aster & Row Support Agent Demo](docs/demo.gif)
```

For a video hosted externally:

```markdown
[Watch the Aster & Row Support Agent Demo](YOUR_VIDEO_LINK)
```

---

## 22. Evaluation Case Inventory

The final evaluation contains 20 cases:

### Supplied visible cases

```text
standard-return-window
trailplus-return-window
final-sale-damaged-exception
canada-multiturn
unsupported-country
valid-order-lookup
missing-order-id
cancelled-order-stale-eta
unknown-order
shipped-without-eta
order-data-privacy
no-lifetime-warranty
retrieved-prompt-injection
insufficient-information
genuine-active-source-conflict
```

### Original regression cases

```text
original-lowercase-order-id
original-order-followup-context
original-final-sale-change-of-mind
original-internal-risk-score
original-cancelled-order-followup
```

This provides coverage beyond the supplied visible wording and specifically tests additional order normalization, privacy, final-sale, and conversation-context behavior.

---

## 23. Final Verification

From a clean checkout, verify the environment and run:

```powershell
python -m py_compile app/agent.py
python -m py_compile app/agent_workflow.py
```

Then:

```powershell
pytest -q
```

Finally:

```powershell
python evaluation/run_evaluation.py
```

Expected evaluation result:

```text
Overall: 20/20 passed
```

Before pushing to GitHub:

```powershell
git status
```

Verify that no secrets are tracked.

The repository should not contain:

```text
.env
API keys
credentials
.venv/
__pycache__/
```

The repository should contain the safe template:

```text
.env.example
```

---

## 24. Submission Checklist

Before submitting the GitHub repository, confirm:

- [x] Application source code included.
- [x] Knowledge-base documents included.
- [x] Mock order data included.
- [x] Tests included.
- [x] 15 supplied visible evaluation cases covered.
- [x] 5 original evaluation cases added.
- [x] Deterministic evaluation suite included.
- [x] Individual evaluation results reported.
- [x] Category-level evaluation results reported.
- [x] Final evaluation is 20/20.
- [x] Baseline result documented.
- [x] Bug diary includes reproduced failures, root causes, fixes, and regression coverage.
- [x] AI coding tools disclosed.
- [x] Incorrect/incomplete AI suggestion documented.
- [x] Known limitations documented.
- [x] Setup instructions documented.
- [x] Environment variables documented.
- [x] `.env.example` contains no real credentials.
- [x] Observability/debug behavior documented.
- [ ] 2–4 minute GIF/video added to README.
- [ ] Final GitHub push verified.

---

## 25. Final Status

The core implementation is complete and the complete expanded evaluation suite currently passes:

```text
20/20 passed
```

The completed reliability areas include:

- Retrieval
- Source grounding
- Authoritative policy handling
- Order lookup
- Order privacy
- Order reliability
- Multi-turn context
- Prompt-injection protection
- Safe abstention
- Source-conflict handling
- Human handoff
- Regression evaluation

The remaining submission-specific task is to add the final demo GIF/video, verify the README/media link on GitHub, and perform the final repository push.
