# HAMMER Spec JSON Schema

> **Auto-generated from Pydantic models.** Regenerate with: `hammer schema`

```json
{
  "$defs": {
    "BehavioralContracts": {
      "properties": {
        "packages": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/PackageContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Packages"
        },
        "pip_packages": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/PipPackageContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Pip Packages"
        },
        "services": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/ServiceContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Services"
        },
        "users": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/UserContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Users"
        },
        "groups": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/GroupContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Groups"
        },
        "firewall": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/FirewallContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Firewall"
        },
        "files": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/FilesContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Files"
        },
        "reachability": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/ReachabilityContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Reachability"
        },
        "http_endpoints": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/HttpEndpointContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Http Endpoints"
        },
        "external_http": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/ExternalHttpContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "External Http"
        },
        "output_checks": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/OutputContract"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Output Checks"
        }
      },
      "title": "BehavioralContracts",
      "type": "object"
    },
    "Binding": {
      "properties": {
        "type": {
          "enum": [
            "service_listen_port",
            "firewall_port_open",
            "template_contains",
            "file_contains",
            "file_exists",
            "file_mode",
            "file_owner"
          ],
          "title": "Type",
          "type": "string"
        },
        "target": {
          "anyOf": [
            {
              "$ref": "#/$defs/ServiceListenTarget"
            },
            {
              "$ref": "#/$defs/FirewallPortTarget"
            },
            {
              "$ref": "#/$defs/FilePatternTarget"
            },
            {
              "$ref": "#/$defs/FilePathTarget"
            },
            {
              "$ref": "#/$defs/FileModeTarget"
            },
            {
              "$ref": "#/$defs/FileOwnerTarget"
            }
          ],
          "title": "Target"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "type",
        "target"
      ],
      "title": "Binding",
      "type": "object"
    },
    "Dependency": {
      "properties": {
        "from_host": {
          "title": "From Host",
          "type": "string"
        },
        "to_host": {
          "title": "To Host",
          "type": "string"
        },
        "kind": {
          "enum": [
            "reachability",
            "ordering"
          ],
          "title": "Kind",
          "type": "string"
        }
      },
      "required": [
        "from_host",
        "to_host",
        "kind"
      ],
      "title": "Dependency",
      "type": "object"
    },
    "Entrypoints": {
      "properties": {
        "playbook_path": {
          "title": "Playbook Path",
          "type": "string"
        },
        "required_roles": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Required Roles"
        },
        "required_files": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Required Files"
        },
        "provided_files": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/ProvidedFile"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Provided Files"
        }
      },
      "required": [
        "playbook_path"
      ],
      "title": "Entrypoints",
      "type": "object"
    },
    "ExpectedRunsSet": {
      "properties": {
        "baseline": {
          "enum": [
            "zero",
            "at_least_once",
            "exactly_once"
          ],
          "title": "Baseline",
          "type": "string"
        },
        "mutation": {
          "enum": [
            "zero",
            "at_least_once",
            "exactly_once"
          ],
          "title": "Mutation",
          "type": "string"
        },
        "idempotence": {
          "enum": [
            "zero",
            "at_least_once",
            "exactly_once"
          ],
          "title": "Idempotence",
          "type": "string"
        }
      },
      "required": [
        "baseline",
        "mutation",
        "idempotence"
      ],
      "title": "ExpectedRunsSet",
      "type": "object"
    },
    "ExternalHttpContract": {
      "description": "Contract for verifying HTTP endpoints from external perspective.",
      "properties": {
        "url": {
          "title": "Url",
          "type": "string"
        },
        "method": {
          "default": "GET",
          "enum": [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "HEAD"
          ],
          "title": "Method",
          "type": "string"
        },
        "expected_status": {
          "default": 200,
          "maximum": 599,
          "minimum": 100,
          "title": "Expected Status",
          "type": "integer"
        },
        "response_contains": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Response Contains"
        },
        "response_regex": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Response Regex"
        },
        "timeout_seconds": {
          "default": 10,
          "maximum": 60,
          "minimum": 1,
          "title": "Timeout Seconds",
          "type": "integer"
        },
        "from_host": {
          "default": false,
          "title": "From Host",
          "type": "boolean"
        },
        "from_node": {
          "anyOf": [
            {
              "$ref": "#/$defs/NodeSelector"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "url"
      ],
      "title": "ExternalHttpContract",
      "type": "object"
    },
    "FailurePolicy": {
      "description": "Policy for handling expected failures during converge.",
      "properties": {
        "allow_failures": {
          "default": false,
          "title": "Allow Failures",
          "type": "boolean"
        },
        "max_failures": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Max Failures"
        },
        "expected_patterns": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Expected Patterns"
        }
      },
      "title": "FailurePolicy",
      "type": "object"
    },
    "FeatureFlags": {
      "properties": {
        "vault": {
          "default": false,
          "title": "Vault",
          "type": "boolean"
        },
        "selinux": {
          "default": false,
          "title": "Selinux",
          "type": "boolean"
        },
        "handlers": {
          "default": true,
          "title": "Handlers",
          "type": "boolean"
        },
        "reachability": {
          "default": false,
          "title": "Reachability",
          "type": "boolean"
        }
      },
      "title": "FeatureFlags",
      "type": "object"
    },
    "FileContractItem": {
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "present": {
          "title": "Present",
          "type": "boolean"
        },
        "is_directory": {
          "default": false,
          "title": "Is Directory",
          "type": "boolean"
        },
        "mode": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Mode"
        },
        "owner": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Owner"
        },
        "group": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Group"
        },
        "content_regex": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Content Regex"
        }
      },
      "required": [
        "path",
        "present"
      ],
      "title": "FileContractItem",
      "type": "object"
    },
    "FileModeTarget": {
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "mode": {
          "title": "Mode",
          "type": "string"
        }
      },
      "required": [
        "path",
        "mode"
      ],
      "title": "FileModeTarget",
      "type": "object"
    },
    "FileOwnerTarget": {
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "owner": {
          "title": "Owner",
          "type": "string"
        },
        "group": {
          "title": "Group",
          "type": "string"
        }
      },
      "required": [
        "path",
        "owner",
        "group"
      ],
      "title": "FileOwnerTarget",
      "type": "object"
    },
    "FilePathTarget": {
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        }
      },
      "required": [
        "path"
      ],
      "title": "FilePathTarget",
      "type": "object"
    },
    "FilePatternTarget": {
      "properties": {
        "path": {
          "title": "Path",
          "type": "string"
        },
        "pattern": {
          "title": "Pattern",
          "type": "string"
        }
      },
      "required": [
        "path",
        "pattern"
      ],
      "title": "FilePatternTarget",
      "type": "object"
    },
    "FilesContract": {
      "properties": {
        "items": {
          "items": {
            "$ref": "#/$defs/FileContractItem"
          },
          "title": "Items",
          "type": "array"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "items",
        "node_selector"
      ],
      "title": "FilesContract",
      "type": "object"
    },
    "FirewallContract": {
      "properties": {
        "open_ports": {
          "items": {
            "$ref": "#/$defs/FirewallPort"
          },
          "title": "Open Ports",
          "type": "array"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "firewall_type": {
          "default": "firewalld",
          "enum": [
            "firewalld",
            "iptables"
          ],
          "title": "Firewall Type",
          "type": "string"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "open_ports",
        "node_selector"
      ],
      "title": "FirewallContract",
      "type": "object"
    },
    "FirewallPort": {
      "properties": {
        "port": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "$ref": "#/$defs/PortRefVar"
            }
          ],
          "title": "Port"
        },
        "protocol": {
          "enum": [
            "tcp",
            "udp"
          ],
          "title": "Protocol",
          "type": "string"
        },
        "zone": {
          "title": "Zone",
          "type": "string"
        }
      },
      "required": [
        "port",
        "protocol",
        "zone"
      ],
      "title": "FirewallPort",
      "type": "object"
    },
    "FirewallPortTarget": {
      "properties": {
        "zone": {
          "title": "Zone",
          "type": "string"
        },
        "protocol": {
          "enum": [
            "tcp",
            "udp"
          ],
          "title": "Protocol",
          "type": "string"
        }
      },
      "required": [
        "zone",
        "protocol"
      ],
      "title": "FirewallPortTarget",
      "type": "object"
    },
    "ForwardedPort": {
      "properties": {
        "host_port": {
          "maximum": 65535,
          "minimum": 1,
          "title": "Host Port",
          "type": "integer"
        },
        "guest_port": {
          "maximum": 65535,
          "minimum": 1,
          "title": "Guest Port",
          "type": "integer"
        },
        "protocol": {
          "enum": [
            "tcp",
            "udp"
          ],
          "title": "Protocol",
          "type": "string"
        }
      },
      "required": [
        "host_port",
        "guest_port",
        "protocol"
      ],
      "title": "ForwardedPort",
      "type": "object"
    },
    "GroupContract": {
      "description": "Contract for verifying system groups exist with specified properties.",
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "exists": {
          "default": true,
          "title": "Exists",
          "type": "boolean"
        },
        "gid": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Gid"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "name",
        "node_selector"
      ],
      "title": "GroupContract",
      "type": "object"
    },
    "HandlerContract": {
      "properties": {
        "handler_name": {
          "title": "Handler Name",
          "type": "string"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "handler_target": {
          "$ref": "#/$defs/HandlerTarget"
        },
        "trigger_conditions": {
          "items": {
            "anyOf": [
              {
                "$ref": "#/$defs/TriggerFileChanged"
              },
              {
                "$ref": "#/$defs/TriggerTemplateChanged"
              },
              {
                "$ref": "#/$defs/TriggerVariableChanged"
              }
            ]
          },
          "title": "Trigger Conditions",
          "type": "array"
        },
        "non_trigger_conditions": {
          "items": {
            "anyOf": [
              {
                "$ref": "#/$defs/NonTriggerNoop"
              },
              {
                "$ref": "#/$defs/NonTriggerUnrelatedFile"
              }
            ]
          },
          "title": "Non Trigger Conditions",
          "type": "array"
        },
        "expected_runs": {
          "$ref": "#/$defs/ExpectedRunsSet"
        },
        "weight": {
          "default": 2.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "handler_name",
        "node_selector",
        "handler_target",
        "trigger_conditions",
        "non_trigger_conditions",
        "expected_runs"
      ],
      "title": "HandlerContract",
      "type": "object"
    },
    "HandlerTarget": {
      "properties": {
        "service": {
          "title": "Service",
          "type": "string"
        },
        "action": {
          "enum": [
            "restart",
            "reload"
          ],
          "title": "Action",
          "type": "string"
        }
      },
      "required": [
        "service",
        "action"
      ],
      "title": "HandlerTarget",
      "type": "object"
    },
    "HttpEndpointContract": {
      "description": "Contract for verifying HTTP endpoints return expected responses.",
      "properties": {
        "url": {
          "title": "Url",
          "type": "string"
        },
        "method": {
          "default": "GET",
          "enum": [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "HEAD"
          ],
          "title": "Method",
          "type": "string"
        },
        "expected_status": {
          "default": 200,
          "maximum": 599,
          "minimum": 100,
          "title": "Expected Status",
          "type": "integer"
        },
        "response_contains": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Response Contains"
        },
        "response_regex": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Response Regex"
        },
        "timeout_seconds": {
          "default": 5,
          "maximum": 60,
          "minimum": 1,
          "title": "Timeout Seconds",
          "type": "integer"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "url",
        "node_selector"
      ],
      "title": "HttpEndpointContract",
      "type": "object"
    },
    "IdempotenceEnforcement": {
      "properties": {
        "require_changed_zero": {
          "default": true,
          "title": "Require Changed Zero",
          "type": "boolean"
        },
        "require_no_handlers": {
          "default": true,
          "title": "Require No Handlers",
          "type": "boolean"
        }
      },
      "title": "IdempotenceEnforcement",
      "type": "object"
    },
    "IdempotencePolicy": {
      "properties": {
        "required": {
          "default": true,
          "title": "Required",
          "type": "boolean"
        },
        "allowed_changes": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Allowed Changes"
        },
        "enforcement": {
          "anyOf": [
            {
              "$ref": "#/$defs/IdempotenceEnforcement"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "title": "IdempotencePolicy",
      "type": "object"
    },
    "Node": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "groups": {
          "items": {
            "type": "string"
          },
          "title": "Groups",
          "type": "array"
        },
        "resources": {
          "$ref": "#/$defs/NodeResources"
        },
        "forwarded_ports": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/ForwardedPort"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Forwarded Ports"
        }
      },
      "required": [
        "name",
        "groups",
        "resources"
      ],
      "title": "Node",
      "type": "object"
    },
    "NodeResources": {
      "properties": {
        "cpu": {
          "maximum": 64,
          "minimum": 1,
          "title": "Cpu",
          "type": "integer"
        },
        "ram_mb": {
          "maximum": 262144,
          "minimum": 256,
          "title": "Ram Mb",
          "type": "integer"
        }
      },
      "required": [
        "cpu",
        "ram_mb"
      ],
      "title": "NodeResources",
      "type": "object"
    },
    "NodeSelector": {
      "properties": {
        "group": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Group"
        },
        "host": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Host"
        }
      },
      "title": "NodeSelector",
      "type": "object"
    },
    "NonTriggerNoop": {
      "properties": {
        "noop_rerun": {
          "const": true,
          "title": "Noop Rerun",
          "type": "boolean"
        }
      },
      "required": [
        "noop_rerun"
      ],
      "title": "NonTriggerNoop",
      "type": "object"
    },
    "NonTriggerUnrelatedFile": {
      "properties": {
        "unrelated_file_changed": {
          "title": "Unrelated File Changed",
          "type": "string"
        }
      },
      "required": [
        "unrelated_file_changed"
      ],
      "title": "NonTriggerUnrelatedFile",
      "type": "object"
    },
    "OutputContract": {
      "description": "Contract for verifying Ansible output contains expected patterns.",
      "properties": {
        "pattern": {
          "title": "Pattern",
          "type": "string"
        },
        "match_type": {
          "default": "contains",
          "enum": [
            "contains",
            "regex"
          ],
          "title": "Match Type",
          "type": "string"
        },
        "expected": {
          "default": true,
          "title": "Expected",
          "type": "boolean"
        },
        "description": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Description"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "pattern"
      ],
      "title": "OutputContract",
      "type": "object"
    },
    "OverlayTarget": {
      "properties": {
        "overlay_kind": {
          "enum": [
            "group_vars",
            "host_vars",
            "inventory_vars",
            "extra_vars"
          ],
          "title": "Overlay Kind",
          "type": "string"
        },
        "target_name": {
          "title": "Target Name",
          "type": "string"
        }
      },
      "required": [
        "overlay_kind",
        "target_name"
      ],
      "title": "OverlayTarget",
      "type": "object"
    },
    "PackageContract": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "state": {
          "enum": [
            "present",
            "absent"
          ],
          "title": "State",
          "type": "string"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "name",
        "state",
        "node_selector"
      ],
      "title": "PackageContract",
      "type": "object"
    },
    "PhaseOverlay": {
      "properties": {
        "inventory_vars": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Inventory Vars"
        },
        "group_vars": {
          "anyOf": [
            {
              "additionalProperties": {
                "additionalProperties": true,
                "type": "object"
              },
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Group Vars"
        },
        "host_vars": {
          "anyOf": [
            {
              "additionalProperties": {
                "additionalProperties": true,
                "type": "object"
              },
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Host Vars"
        },
        "extra_vars": {
          "anyOf": [
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Extra Vars"
        },
        "reboot": {
          "anyOf": [
            {
              "$ref": "#/$defs/RebootConfig"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "failure_policy": {
          "anyOf": [
            {
              "$ref": "#/$defs/FailurePolicy"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "title": "PhaseOverlay",
      "type": "object"
    },
    "PhaseOverlays": {
      "properties": {
        "baseline": {
          "anyOf": [
            {
              "$ref": "#/$defs/PhaseOverlay"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "mutation": {
          "anyOf": [
            {
              "$ref": "#/$defs/PhaseOverlay"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "title": "PhaseOverlays",
      "type": "object"
    },
    "PipPackageContract": {
      "description": "Contract for verifying pip packages are installed.",
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "state": {
          "default": "present",
          "enum": [
            "present",
            "absent"
          ],
          "title": "State",
          "type": "string"
        },
        "python": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Python"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "name",
        "node_selector"
      ],
      "title": "PipPackageContract",
      "type": "object"
    },
    "PortRefVar": {
      "properties": {
        "var": {
          "title": "Var",
          "type": "string"
        }
      },
      "required": [
        "var"
      ],
      "title": "PortRefVar",
      "type": "object"
    },
    "PrecedenceScenario": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "variable": {
          "title": "Variable",
          "type": "string"
        },
        "layers": {
          "items": {
            "enum": [
              "role_default",
              "role_vars",
              "play_vars",
              "vars_files",
              "inventory_vars",
              "group_vars",
              "host_vars",
              "extra_vars"
            ],
            "type": "string"
          },
          "title": "Layers",
          "type": "array"
        },
        "expected_winner": {
          "enum": [
            "role_default",
            "role_vars",
            "play_vars",
            "vars_files",
            "inventory_vars",
            "group_vars",
            "host_vars",
            "extra_vars"
          ],
          "title": "Expected Winner",
          "type": "string"
        },
        "bindings_to_verify": {
          "items": {
            "type": "integer"
          },
          "title": "Bindings To Verify",
          "type": "array"
        },
        "phase": {
          "default": "baseline",
          "enum": [
            "baseline",
            "mutation"
          ],
          "title": "Phase",
          "type": "string"
        }
      },
      "required": [
        "name",
        "variable",
        "layers",
        "expected_winner",
        "bindings_to_verify"
      ],
      "title": "PrecedenceScenario",
      "type": "object"
    },
    "ProvidedFile": {
      "description": "A file provided by the assignment to students.",
      "properties": {
        "source": {
          "title": "Source",
          "type": "string"
        },
        "destination": {
          "title": "Destination",
          "type": "string"
        }
      },
      "required": [
        "source",
        "destination"
      ],
      "title": "ProvidedFile",
      "type": "object"
    },
    "ReachabilityContract": {
      "properties": {
        "from_host": {
          "title": "From Host",
          "type": "string"
        },
        "to_host": {
          "title": "To Host",
          "type": "string"
        },
        "protocol": {
          "enum": [
            "tcp",
            "udp"
          ],
          "title": "Protocol",
          "type": "string"
        },
        "port": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "$ref": "#/$defs/PortRefVar"
            }
          ],
          "title": "Port"
        },
        "expectation": {
          "enum": [
            "reachable",
            "not_reachable"
          ],
          "title": "Expectation",
          "type": "string"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "from_host",
        "to_host",
        "protocol",
        "port",
        "expectation"
      ],
      "title": "ReachabilityContract",
      "type": "object"
    },
    "RebootConfig": {
      "description": "Configuration for rebooting nodes after converge, before tests.",
      "properties": {
        "enabled": {
          "default": false,
          "title": "Enabled",
          "type": "boolean"
        },
        "nodes": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Nodes"
        },
        "timeout": {
          "default": 120,
          "maximum": 600,
          "minimum": 30,
          "title": "Timeout",
          "type": "integer"
        },
        "poll_interval": {
          "default": 5,
          "maximum": 30,
          "minimum": 1,
          "title": "Poll Interval",
          "type": "integer"
        }
      },
      "title": "RebootConfig",
      "type": "object"
    },
    "ServiceContract": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "enabled": {
          "title": "Enabled",
          "type": "boolean"
        },
        "running": {
          "title": "Running",
          "type": "boolean"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "name",
        "enabled",
        "running",
        "node_selector"
      ],
      "title": "ServiceContract",
      "type": "object"
    },
    "ServiceListenTarget": {
      "properties": {
        "service": {
          "title": "Service",
          "type": "string"
        },
        "protocol": {
          "enum": [
            "tcp",
            "udp"
          ],
          "title": "Protocol",
          "type": "string"
        },
        "address": {
          "title": "Address",
          "type": "string"
        }
      },
      "required": [
        "service",
        "protocol",
        "address"
      ],
      "title": "ServiceListenTarget",
      "type": "object"
    },
    "Topology": {
      "properties": {
        "domain": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Domain"
        },
        "nodes": {
          "items": {
            "$ref": "#/$defs/Node"
          },
          "title": "Nodes",
          "type": "array"
        },
        "forwarded_ports": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/ForwardedPort"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Forwarded Ports"
        },
        "dependencies": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/Dependency"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Dependencies"
        }
      },
      "required": [
        "nodes"
      ],
      "title": "Topology",
      "type": "object"
    },
    "TriggerFileChanged": {
      "properties": {
        "file_changed": {
          "title": "File Changed",
          "type": "string"
        }
      },
      "required": [
        "file_changed"
      ],
      "title": "TriggerFileChanged",
      "type": "object"
    },
    "TriggerTemplateChanged": {
      "properties": {
        "template_changed": {
          "title": "Template Changed",
          "type": "string"
        }
      },
      "required": [
        "template_changed"
      ],
      "title": "TriggerTemplateChanged",
      "type": "object"
    },
    "TriggerVariableChanged": {
      "properties": {
        "variable_changed": {
          "title": "Variable Changed",
          "type": "string"
        }
      },
      "required": [
        "variable_changed"
      ],
      "title": "TriggerVariableChanged",
      "type": "object"
    },
    "UserContract": {
      "description": "Contract for verifying system users exist with specified properties.",
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "exists": {
          "default": true,
          "title": "Exists",
          "type": "boolean"
        },
        "uid": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Uid"
        },
        "gid": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Gid"
        },
        "home": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Home"
        },
        "shell": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Shell"
        },
        "groups": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Groups"
        },
        "node_selector": {
          "$ref": "#/$defs/NodeSelector"
        },
        "phases": {
          "anyOf": [
            {
              "items": {
                "enum": [
                  "baseline",
                  "mutation",
                  "idempotence"
                ],
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Phases"
        },
        "weight": {
          "default": 1.0,
          "minimum": 0.0,
          "title": "Weight",
          "type": "number"
        }
      },
      "required": [
        "name",
        "node_selector"
      ],
      "title": "UserContract",
      "type": "object"
    },
    "VariableContract": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "type": {
          "enum": [
            "int",
            "string",
            "bool",
            "list",
            "dict"
          ],
          "title": "Type",
          "type": "string"
        },
        "defaults": {
          "$ref": "#/$defs/VariableDefaults"
        },
        "allowed_values": {
          "items": {},
          "title": "Allowed Values",
          "type": "array"
        },
        "grading_overlay_targets": {
          "items": {
            "$ref": "#/$defs/OverlayTarget"
          },
          "title": "Grading Overlay Targets",
          "type": "array"
        },
        "binding_targets": {
          "items": {
            "$ref": "#/$defs/Binding"
          },
          "title": "Binding Targets",
          "type": "array"
        },
        "bindings_mode": {
          "default": "all",
          "enum": [
            "all",
            "any"
          ],
          "title": "Bindings Mode",
          "type": "string"
        }
      },
      "required": [
        "name",
        "type",
        "defaults",
        "allowed_values",
        "grading_overlay_targets",
        "binding_targets"
      ],
      "title": "VariableContract",
      "type": "object"
    },
    "VariableDefaults": {
      "properties": {
        "student": {
          "title": "Student"
        }
      },
      "required": [
        "student"
      ],
      "title": "VariableDefaults",
      "type": "object"
    },
    "VaultSpec": {
      "properties": {
        "vault_password": {
          "title": "Vault Password",
          "type": "string"
        },
        "vault_ids": {
          "anyOf": [
            {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Vault Ids"
        },
        "vaulted_vars_files": {
          "items": {
            "type": "string"
          },
          "title": "Vaulted Vars Files",
          "type": "array"
        },
        "vaulted_variables": {
          "items": {
            "type": "string"
          },
          "title": "Vaulted Variables",
          "type": "array"
        },
        "bindings_to_verify": {
          "items": {
            "type": "integer"
          },
          "title": "Bindings To Verify",
          "type": "array"
        }
      },
      "required": [
        "vault_password",
        "vaulted_vars_files",
        "vaulted_variables",
        "bindings_to_verify"
      ],
      "title": "VaultSpec",
      "type": "object"
    }
  },
  "properties": {
    "assignment_id": {
      "title": "Assignment Id",
      "type": "string"
    },
    "assignment_version": {
      "title": "Assignment Version",
      "type": "string"
    },
    "spec_version": {
      "const": "1.0",
      "title": "Spec Version",
      "type": "string"
    },
    "seed": {
      "title": "Seed",
      "type": "integer"
    },
    "provider": {
      "const": "libvirt",
      "title": "Provider",
      "type": "string"
    },
    "os": {
      "const": "almalinux9",
      "title": "Os",
      "type": "string"
    },
    "features": {
      "$ref": "#/$defs/FeatureFlags"
    },
    "topology": {
      "$ref": "#/$defs/Topology"
    },
    "entrypoints": {
      "$ref": "#/$defs/Entrypoints"
    },
    "variable_contracts": {
      "anyOf": [
        {
          "items": {
            "$ref": "#/$defs/VariableContract"
          },
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Variable Contracts"
    },
    "precedence_scenarios": {
      "anyOf": [
        {
          "items": {
            "$ref": "#/$defs/PrecedenceScenario"
          },
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Precedence Scenarios"
    },
    "behavioral_contracts": {
      "anyOf": [
        {
          "$ref": "#/$defs/BehavioralContracts"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "handler_contracts": {
      "anyOf": [
        {
          "items": {
            "$ref": "#/$defs/HandlerContract"
          },
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "title": "Handler Contracts"
    },
    "idempotence": {
      "$ref": "#/$defs/IdempotencePolicy"
    },
    "vault": {
      "anyOf": [
        {
          "$ref": "#/$defs/VaultSpec"
        },
        {
          "type": "null"
        }
      ],
      "default": null
    },
    "phase_overlays": {
      "$ref": "#/$defs/PhaseOverlays"
    }
  },
  "required": [
    "assignment_id",
    "assignment_version",
    "spec_version",
    "seed",
    "provider",
    "os",
    "topology",
    "entrypoints",
    "idempotence",
    "phase_overlays"
  ],
  "title": "HammerSpec",
  "type": "object"
}
```
