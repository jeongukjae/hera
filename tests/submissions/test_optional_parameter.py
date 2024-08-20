from typing import Optional

import pytest

from hera.workflows import Steps, Workflow, WorkflowsService, script


@script()
def print_msg(message: Optional[str] = None):
    print(message)


def get_workflow() -> Workflow:
    with Workflow(
        generate_name="optional-param-",
        entrypoint="steps",
        namespace="argo",
        workflows_service=WorkflowsService(
            host="https://localhost:2746",
            namespace="argo",
            verify_ssl=False,
        ),
    ) as w:
        with Steps(name="steps"):
            print_msg(name="step-1", arguments={"message": "Hello world!"})
            print_msg(name="step-2", arguments={})
            print_msg(name="step-3")

    return w


@pytest.mark.on_cluster
def test_create_workflow_with_optional_parameter():
    model_workflow = get_workflow().create(wait=True)
    assert model_workflow.status and model_workflow.status.phase == "Succeeded"
