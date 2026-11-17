---
type: llm
focus: trace
weight: 1
---

Statements about what the existing code does are correct. Check at least these against app.py, and fail if the spec states any of them wrongly: cancelling a visit deletes the row (and the delete itself has no status condition); a host's own visits, past ones included, are listed on /visits/mine; the front desk page lists only today's visits; marking arrival or departure a second time changes nothing; only administrators can export.
