package agent

default allow := false

# The identity is authenticated by mTLS and independently checked by the MCP app.
# Only this workload can call the listed tools.
allow if {
    input.subject == "spiffe://example.internal/agent/primary"
    input.action in {"search_knowledge", "create_report"}
}
