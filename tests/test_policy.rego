package agent

import rego.v1

test_primary_agent_can_search if {
  allow with input as {
    "subject": "spiffe://example.internal/agent/primary",
    "action": "search_knowledge"
  }
}

test_unknown_agent_denied if {
  not allow with input as {
    "subject": "spiffe://example.internal/agent/unknown",
    "action": "search_knowledge"
  }
}

test_disallowed_tool_denied if {
  not allow with input as {
    "subject": "spiffe://example.internal/agent/primary",
    "action": "delete_database"
  }
}
