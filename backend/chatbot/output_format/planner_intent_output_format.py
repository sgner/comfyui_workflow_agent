from typing import TypedDict


class user_intent(TypedDict):
    core_function: str
    type: str
    details: list[str]
    base_model: str
    clarification_needed: bool


class current_workflow_summary(TypedDict):
    base_model: str
    key_nodes: list[dict[str, str]]
    workflow_stage: str
    input_output: object
    potential_issues: list[str]


class planning_suggestions(TypedDict):
    integration_point: str
    expected_nodes: list[str]
    parameters_guidelines: object
    dependencies: list[str]


class output_format(TypedDict):
    user_intent: user_intent
    current_workflow_summary: current_workflow_summary
    planning_suggestions: planning_suggestions
    notes: str
