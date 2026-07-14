# TODO_CHATBOT_ROADMAP (School ERP)

## Status
- AI chatbot abhi **direct** writes karta hai (regex-based write intent detect → ORM execute)
- Roadmap wala **confirm-before-write** + **tool registry** chat layer me abhi effectively missing hai

## Why
- `chat/consumers.py` websocket flow: user message save → `get_ai_response()` → assistant reply save
- `chat/ai_service.py` flow: **Step 2** write intent detect + `_execute_*_action()` execute **direct** (no PendingAction gate)

## Phase 1: PendingAction propose/confirm gate (MVP)
### 1. Add/verify PendingAction model
- `PendingAction` model: session(FK), tool_name, params(JSON), status(Pending/Confirmed/Cancelled), created_at
- ensure migration exists

### 2. Change WRITE flow in `chat/ai_service.py`
Current: `_detect_write_intent()` → `_execute_*_action()` → immediate ORM write

New:
- detect write intent
- instead of executing ORM:
  - create `PendingAction(status='Pending', tool_name=..., params=...)`
  - return AI reply: summary + ask user to `confirm` / `cancel`

### 3. Change websocket consumer `chat/consumers.py`
- If message is `confirm` and there is active `PendingAction` for session:
  - execute tool using stored params
  - delete/cancel PendingAction
- If message is `cancel`:
  - delete/cancel PendingAction
- Else:
  - call `get_ai_response()` normally

## Phase 2: Role-based tool registry
### 4. Build ToolRegistry
- role → allowed tool set
- Teacher: allow attendance/marks/behavior write tools only
- Student: allow complaint + certificate request write tools only
- Parent: allow complaint + message_teacher only

### 5. Enforce in chat layer
- `get_ai_response()` should only detect/permit tools from registry
- tool execution should re-check role + instance scoping

## Phase 3: Multi-LLM fallback strictness
### 6. Implement error-type aware fallback
- Gemini/OpenRouter switch **only** when error is quota/rate-limit (HTTP 429 / ResourceExhausted)
- logic errors (bad tool params) do not retry across models

## Phase 4: Tests
### 7. Add security test matrix
- student requesting other student's data via message text
- teacher marking attendance for class-section not assigned
- parent switching to unlinked child
- admin-only tool call from non-admin role

## Phase 5: UX contract updates
### 8. Confirm UI contract
- “Confirm” message format (exact string/intent)
- payload schema returned for PendingAction (summary)

## Notes
Current key files:
- `chat/consumers.py`
- `chat/ai_service.py`
- `attendance/views/teacher.py` (API layer has proper scoping checks)

