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

"""Tests for the tool, custom, transform and sub-workflow node kinds."""

import pytest
import yaml
from pydantic import ValidationError

from codemie_sdk.builders.workflow import WorkflowBuilder
from codemie_sdk.builders.workflow.definition import (
    CustomWorkflowNode,
    WorkflowMCPServer,
    WorkflowNextState,
    WorkflowTool,
)


def _rendered(builder: WorkflowBuilder) -> dict:
    return yaml.safe_load(builder.render().to_yaml_config())


def _state(rendered: dict, state_id: str) -> dict:
    return next(s for s in rendered["states"] if s["id"] == state_id)


class TestWorkflowToolModel:
    def test_requires_id_and_tool(self):
        with pytest.raises(ValidationError):
            WorkflowTool(tool="search")
        with pytest.raises(ValidationError):
            WorkflowTool(id="search")

    def test_rejects_unknown_field(self):
        with pytest.raises(ValidationError):
            WorkflowTool(id="a", tool="b", tol_args={})


class TestCustomWorkflowNodeModel:
    def test_requires_id_and_custom_node_id(self):
        with pytest.raises(ValidationError):
            CustomWorkflowNode(custom_node_id="transform_node")
        with pytest.raises(ValidationError):
            CustomWorkflowNode(id="shape")


class TestToolNode:
    def test_add_tool_renders_catalog_entry(self):
        builder = WorkflowBuilder("wf").add_tool(
            "find_sources",
            "_search_files_by_regex",
            tool_args={"path": "src"},
            integration_alias="my-plugin-integration",
        )
        tools = _rendered(builder)["tools"]
        assert tools == [
            {
                "id": "find_sources",
                "tool": "_search_files_by_regex",
                "tool_args": {"path": "src"},
                "integration_alias": "my-plugin-integration",
                "trace": False,
                "resolve_dynamic_values_in_response": False,
            }
        ]

    def test_add_tool_with_mcp_server_renders_nested_server(self):
        builder = WorkflowBuilder("wf").add_tool(
            "run_command",
            "run_command",
            mcp_server=WorkflowMCPServer(
                name="CLI MCP Server",
                description="Runs shell commands",
                mcp_connect_url="http://mcp-connect:3000",
                integration_alias="cli-mcp-integration",
                config={"command": "uvx", "args": ["cli-mcp-server"]},
            ),
        )
        server = _rendered(builder)["tools"][0]["mcp_server"]
        assert server["name"] == "CLI MCP Server"
        assert server["mcp_connect_url"] == "http://mcp-connect:3000"
        assert server["integration_alias"] == "cli-mcp-integration"
        assert server["config"]["command"] == "uvx"
        assert server["config"]["args"] == ["cli-mcp-server"]

    def test_add_tool_rejects_duplicate_id(self):
        builder = WorkflowBuilder("wf").add_tool("t", "tool_a")
        with pytest.raises(ValueError, match="duplicate tool id: 't'"):
            builder.add_tool("t", "tool_b")

    def test_add_tool_state_references_declared_tool(self):
        builder = (
            WorkflowBuilder("wf")
            .add_tool("find_sources", "_search_files_by_regex")
            .add_tool_state(
                "search",
                "find_sources",
                WorkflowNextState(state_id="end"),
                tool_args={"regex": "[.]py$"},
            )
        )
        state = _state(_rendered(builder), "search")
        assert state["tool_id"] == "find_sources"
        assert state["tool_args"] == {"regex": "[.]py$"}
        assert "assistant_id" not in state

    def test_add_tool_state_rejects_undeclared_tool(self):
        with pytest.raises(ValueError, match="unknown tool id: 'ghost'"):
            WorkflowBuilder("wf").add_tool_state("search", "ghost", WorkflowNextState())


class TestCustomNode:
    def test_add_custom_node_renders_catalog_entry(self):
        builder = WorkflowBuilder("wf").add_custom_node(
            "summary",
            "state_processor_node",
            name="Summary",
            model="gpt-4.1-mini",
            config={"state_id": "review", "output_template": "{{ items }}"},
        )
        assert _rendered(builder)["custom_nodes"] == [
            {
                "id": "summary",
                "custom_node_id": "state_processor_node",
                "name": "Summary",
                "model": "gpt-4.1-mini",
                "config": {"state_id": "review", "output_template": "{{ items }}"},
            }
        ]

    def test_custom_node_kind_defaults_to_its_id(self):
        builder = WorkflowBuilder("wf").add_custom_node("state_processor_node")
        node = _rendered(builder)["custom_nodes"][0]
        assert node["custom_node_id"] == "state_processor_node"

    def test_add_custom_node_rejects_duplicate_id(self):
        builder = WorkflowBuilder("wf").add_custom_node("n", "kind_a")
        with pytest.raises(ValueError, match="duplicate custom node id: 'n'"):
            builder.add_custom_node("n", "kind_b")

    def test_add_custom_node_state_references_declared_node(self):
        builder = (
            WorkflowBuilder("wf")
            .add_custom_node("summary", "state_processor_node")
            .add_custom_node_state(
                "summarize",
                "summary",
                WorkflowNextState(state_id="end"),
                task="Summarize the review results",
            )
        )
        state = _state(_rendered(builder), "summarize")
        assert state["custom_node_id"] == "summary"
        assert state["task"] == "Summarize the review results"

    def test_add_custom_node_state_rejects_undeclared_node(self):
        with pytest.raises(ValueError, match="unknown custom node id: 'ghost'"):
            WorkflowBuilder("wf").add_custom_node_state(
                "s", "ghost", WorkflowNextState()
            )


class TestTransformNode:
    MAPPINGS = [
        {
            "output_field": "title",
            "type": "extract",
            "source_path": "pull_request.title",
        },
        {"output_field": "summary", "type": "template", "template": "PR {{ number }}"},
    ]

    def test_renders_a_transform_custom_node(self):
        builder = WorkflowBuilder("wf").add_transform_node(
            "shape_pr", self.MAPPINGS, name="Shape PR", on_error="fail"
        )
        node = _rendered(builder)["custom_nodes"][0]
        assert node["id"] == "shape_pr"
        assert node["custom_node_id"] == "transform_node"
        assert node["name"] == "Shape PR"
        assert node["config"] == {"mappings": self.MAPPINGS, "on_error": "fail"}

    def test_only_given_options_reach_the_config(self):
        builder = WorkflowBuilder("wf").add_transform_node(
            "shape_pr",
            self.MAPPINGS,
            input_source="messages",
            input_key="payload",
            output_schema={"type": "object"},
            default_output={"title": ""},
            on_error="default",
        )
        config = _rendered(builder)["custom_nodes"][0]["config"]
        assert config == {
            "mappings": self.MAPPINGS,
            "input_source": "messages",
            "input_key": "payload",
            "output_schema": {"type": "object"},
            "default_output": {"title": ""},
            "on_error": "default",
        }

    def test_requires_at_least_one_mapping(self):
        with pytest.raises(ValueError, match="at least one mapping"):
            WorkflowBuilder("wf").add_transform_node("shape_pr", [])

    def test_every_mapping_needs_an_output_field(self):
        with pytest.raises(ValueError, match="output_field"):
            WorkflowBuilder("wf").add_transform_node(
                "shape_pr", [{"type": "extract", "source_path": "a"}]
            )

    def test_can_be_run_by_a_custom_node_state(self):
        builder = (
            WorkflowBuilder("wf")
            .add_transform_node("shape_pr", self.MAPPINGS)
            .add_custom_node_state(
                "shape_event",
                "shape_pr",
                WorkflowNextState(state_id="end", output_key="pr"),
            )
        )
        state = _state(_rendered(builder), "shape_event")
        assert state["custom_node_id"] == "shape_pr"
        assert state["next"]["output_key"] == "pr"


class TestSubWorkflowNode:
    def test_add_sub_workflow_state_renders_workflow_id(self):
        builder = WorkflowBuilder("wf").add_sub_workflow_state(
            "run_review", "wf-123", WorkflowNextState(state_id="end")
        )
        state = _state(_rendered(builder), "run_review")
        assert state["workflow_id"] == "wf-123"
        assert "assistant_id" not in state

    def test_supports_retry_and_interrupt(self):
        builder = WorkflowBuilder("wf").add_sub_workflow_state(
            "run_review", "wf-123", WorkflowNextState(), interrupt_before=True
        )
        assert _state(_rendered(builder), "run_review")["interrupt_before"] is True


class TestAcrossNodeKinds:
    def test_state_ids_are_unique_across_every_node_kind(self):
        builder = (
            WorkflowBuilder("wf")
            .add_assistant("a", system_prompt="do a")
            .add_state("step", "a", "task", WorkflowNextState())
        )
        with pytest.raises(ValueError, match="duplicate state id: 'step'"):
            builder.add_sub_workflow_state("step", "wf-1", WorkflowNextState())

        builder = builder.add_tool("t", "tool").add_custom_node("n", "kind")
        with pytest.raises(ValueError, match="duplicate state id: 'step'"):
            builder.add_tool_state("step", "t", WorkflowNextState())
        with pytest.raises(ValueError, match="duplicate state id: 'step'"):
            builder.add_custom_node_state("step", "n", WorkflowNextState())

    def test_new_methods_leave_the_receiver_untouched(self):
        base = WorkflowBuilder("wf")
        base.add_tool("t", "tool")
        base.add_custom_node("n", "kind")
        base.add_transform_node("x", [{"output_field": "a"}])
        definition = base.render()
        assert definition.tools == []
        assert definition.custom_nodes == []

    def test_catalogs_default_to_empty_lists(self):
        rendered = _rendered(
            WorkflowBuilder("wf")
            .add_assistant("a", system_prompt="do a")
            .add_state("s", "a", "task", WorkflowNextState())
        )
        assert rendered["tools"] == []
        assert rendered["custom_nodes"] == []

    def test_mixed_workflow_references_all_resolve(self):
        builder = (
            WorkflowBuilder("wf")
            .add_tool("find", "_search_files_by_regex")
            .add_transform_node("shape", [{"output_field": "a", "type": "extract"}])
            .add_tool_state("search", "find", WorkflowNextState(state_id="reshape"))
            .add_custom_node_state(
                "reshape", "shape", WorkflowNextState(state_id="review")
            )
            .add_sub_workflow_state("review", "wf-123", WorkflowNextState())
        )
        rendered = _rendered(builder)
        tool_ids = {t["id"] for t in rendered["tools"]}
        node_ids = {n["id"] for n in rendered["custom_nodes"]}
        for state in rendered["states"]:
            if "tool_id" in state:
                assert state["tool_id"] in tool_ids
            if "custom_node_id" in state:
                assert state["custom_node_id"] in node_ids
        assert [s["id"] for s in rendered["states"]] == ["search", "reshape", "review"]
