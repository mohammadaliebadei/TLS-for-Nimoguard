package policies_test
import data.policies

test_allowed_tool if { policies.allow with input as {"tool": "read_file", "agent": "primary"} }
test_denied_tool if { not policies.allow with input as {"tool": "delete_everything", "agent": "primary"} }
test_unknown_agent if { not policies.allow with input as {"tool": "read_file", "agent": "unknown"} }
test_fail_closed if { not policies.allow with input as {} }
