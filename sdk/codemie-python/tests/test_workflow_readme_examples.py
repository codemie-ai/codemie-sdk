# Copyright 2026 EPAM Systems, Inc. ("EPAM")
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Regression tests that the README's "Workflow Builder" examples actually
run, not just read plausibly. Each test mirrors one numbered example
(network-touching `publish()` calls excluded) so a future edit that breaks
the flow (e.g. a reused id, or a dropped chained-builder reassignment) fails
here instead of only being discovered by a reader following the docs."""

import pytest
import yaml

from codemie_sdk.builders.workflow import (
    WorkflowAssistantTool,
    WorkflowBuilder,
    WorkflowMCPServer,
    WorkflowMode,
)
from codemie_sdk.builders.workflow.definition import (
    WorkflowNextState,
    WorkflowRetryPolicy,
    WorkflowStateCondition,
    WorkflowStateSwitch,
    WorkflowStateSwitchCondition,
)


def _example_1_builder() -> WorkflowBuilder:
    return (
        WorkflowBuilder("release-notes")
        .with_description("Generate release notes from merged PRs")
        .with_mode(WorkflowMode.SEQUENTIAL)
        .add_assistant("parser", system_prompt="Extract structured PR data.")
        .add_assistant("writer", assistant_id="a1b2c3d4-...")
        .add_state(
            "parse",
            "parser",
            "Extract merged PRs from {{ user_input }}",
            WorkflowNextState(state_id="draft"),
        )
        .add_state("draft", "writer", "Write the release notes", WorkflowNextState())
    )


def test_example_1_builds_and_renders():
    builder = _example_1_builder()
    definition = builder.render()
    yaml_config = definition.to_yaml_config()
    assert yaml.safe_load(yaml_config)["states"]


def test_example_2_name_reference_resolves_or_raises():
    builder = _example_1_builder()
    builder_with_ref = builder.add_assistant_ref(
        "reviewer", assistant_name="Release Notes Reviewer"
    )

    resolved = builder_with_ref.render().to_yaml_config(
        resolve_assistant_name=lambda name: "resolved-id"
    )
    assert "resolved-id" in resolved

    with pytest.raises(ValueError, match="Release Notes Reviewer"):
        builder_with_ref.render().to_yaml_config()


def test_example_3_branches_loops_retries_checkpoints():
    builder = _example_1_builder()

    builder = builder.add_state(
        "check_count",
        "writer",
        "Assemble the notes",
        WorkflowNextState(
            condition=WorkflowStateCondition(
                expression="count > 0", then="publish", otherwise="end"
            )
        ),
    )
    builder = builder.add_state(
        "route",
        "writer",
        "Route by language",
        WorkflowNextState(
            switch=WorkflowStateSwitch(
                cases=[
                    WorkflowStateSwitchCondition(
                        condition="language == 'Java'", state_id="java_path"
                    ),
                    WorkflowStateSwitchCondition(
                        condition="language == 'Python'", state_id="python_path"
                    ),
                ],
                default="end",
            )
        ),
    )
    builder = builder.add_state(
        "summarize",
        "writer",
        "Write a line for {{ iter_item }}",
        WorkflowNextState(state_id="route", iter_key="prs", output_key="lines"),
    )
    builder = builder.add_state(
        "retry_demo",
        "writer",
        "Write the release notes",
        WorkflowNextState(),
        retry_policy=WorkflowRetryPolicy(
            initial_interval=1.0,
            backoff_factor=2.0,
            max_interval=10.0,
            max_attempts=3,
        ),
    )
    builder = builder.add_state(
        "human_review",
        "writer",
        "Assemble the notes",
        WorkflowNextState(),
        interrupt_before=True,
    )
    builder = builder.with_mode(WorkflowMode.AUTONOMOUS)

    definition = builder.render()
    assert definition.mode == WorkflowMode.AUTONOMOUS
    state_ids = {state.id for state in definition.states}
    assert state_ids == {
        "parse",
        "draft",
        "check_count",
        "route",
        "summarize",
        "retry_demo",
        "human_review",
    }
    # Must not raise: proves every add_state() call above used a fresh id.
    definition.to_yaml_config()


# --- "Workflow Node Types" examples -----------------------------------------


def _render(builder: WorkflowBuilder) -> dict:
    return yaml.safe_load(builder.render().to_yaml_config())


def test_node_types_example_1_assistant_with_a_tool():
    builder = (
        WorkflowBuilder("code-helper")
        .add_assistant(
            "helper",
            system_prompt="You answer questions about the project files.",
            tools=[WorkflowAssistantTool(name="_list_directory")],
        )
        .add_state("ask", "helper", "List what is in the project", WorkflowNextState())
    )
    assistant = _render(builder)["assistants"][0]
    assert assistant["tools"] == [{"name": "_list_directory"}]


def test_node_types_example_2_assistant_with_an_external_tool():
    builder = (
        WorkflowBuilder("file-reader")
        .add_assistant(
            "reader",
            system_prompt="You read files from the project.",
            tools=[
                WorkflowAssistantTool(
                    name="_read_file", integration_alias="my-plugin-integration"
                )
            ],
        )
        .add_state("read", "reader", "Read the README", WorkflowNextState())
    )
    assert _render(builder)["assistants"][0]["tools"] == [
        {"name": "_read_file", "integration_alias": "my-plugin-integration"}
    ]


def test_node_types_example_3_assistant_with_mcp_servers():
    builder = (
        WorkflowBuilder("file-helper")
        .add_assistant(
            "files",
            system_prompt="You manage files in the project folder.",
            mcp_servers=[
                WorkflowMCPServer(
                    name="filesystem",
                    config={
                        "command": "mcp-server-filesystem",
                        "args": ["/home/codemie"],
                    },
                ),
                WorkflowMCPServer(
                    name="github", mcp_config_id="your-catalog-config-id"
                ),
            ],
        )
        .add_state("tidy", "files", "Tidy up the project folder", WorkflowNextState())
    )
    servers = _render(builder)["assistants"][0]["mcp_servers"]
    assert [s["name"] for s in servers] == ["filesystem", "github"]
    assert servers[1]["mcp_config_id"] == "your-catalog-config-id"


def test_node_types_example_4_tool_node():
    builder = (
        WorkflowBuilder("find-sources")
        .add_tool(
            "find_sources",
            "_search_files_by_regex",
            integration_alias="my-plugin-integration",
        )
        .add_tool_state(
            "search",
            "find_sources",
            WorkflowNextState(state_id="end"),
            tool_args={"path": "src", "regex": "[.]py$"},
        )
    )
    rendered = _render(builder)
    assert rendered["tools"][0]["id"] == "find_sources"
    assert rendered["states"][0]["tool_id"] == "find_sources"


def test_node_types_example_4_tool_served_by_an_mcp_server():
    builder = WorkflowBuilder("run-commands").add_tool(
        "run_command",
        "run_command",
        mcp_server=WorkflowMCPServer(
            name="CLI MCP Server",
            description="Runs shell commands",
            mcp_connect_url="http://codemie-mcp-connect:3000",
            config={"command": "uvx", "args": ["cli-mcp-server"]},
        ),
    )
    assert _render(builder)["tools"][0]["mcp_server"]["name"] == "CLI MCP Server"


def test_node_types_example_5_custom_node():
    builder = (
        WorkflowBuilder("review-summary")
        .add_custom_node(
            "summary",
            "state_processor_node",
            model="gpt-4.1-mini",
            config={
                "state_id": "review",
                "output_template": "{% for item in items %}- {{ item.file_path }}: {{ item.conclusion }}\n{% endfor %}",
            },
        )
        .add_custom_node_state(
            "summarize",
            "summary",
            WorkflowNextState(state_id="end"),
            task="Summarize the review results",
        )
    )
    rendered = _render(builder)
    assert rendered["custom_nodes"][0]["custom_node_id"] == "state_processor_node"
    assert rendered["states"][0]["custom_node_id"] == "summary"


def test_node_types_example_6_transform_node():
    builder = (
        WorkflowBuilder("shape-pr")
        .add_transform_node(
            "shape_pr",
            mappings=[
                {
                    "output_field": "title",
                    "type": "extract",
                    "source_path": "pull_request.title",
                },
                {
                    "output_field": "summary",
                    "type": "template",
                    "template": "PR #{{ number }} by @{{ pull_request.user.login }}",
                },
                {
                    "output_field": "actionable",
                    "type": "condition",
                    "condition": "action in ['opened', 'reopened']",
                    "then_value": True,
                    "else_value": False,
                },
            ],
            on_error="fail",
        )
        .add_custom_node_state(
            "shape_event",
            "shape_pr",
            WorkflowNextState(state_id="end", output_key="pr"),
            task="Shape the PR event",
        )
    )
    rendered = _render(builder)
    node = rendered["custom_nodes"][0]
    assert node["custom_node_id"] == "transform_node"
    assert [m["output_field"] for m in node["config"]["mappings"]] == [
        "title",
        "summary",
        "actionable",
    ]
    assert rendered["states"][0]["custom_node_id"] == "shape_pr"


def test_node_types_example_7_sub_workflow_node():
    builder = WorkflowBuilder("review-pipeline").add_sub_workflow_state(
        "run_review",
        "your-workflow-id",
        WorkflowNextState(state_id="end"),
    )
    assert _render(builder)["states"][0]["workflow_id"] == "your-workflow-id"
