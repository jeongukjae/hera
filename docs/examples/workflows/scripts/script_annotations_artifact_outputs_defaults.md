# Script Annotations Artifact Outputs Defaults



This example will reuse the outputs volume across script steps.


=== "Hera"

    ```python linenums="1"
    from typing import Annotated

    from hera.workflows import (
        Artifact,
        Parameter,
        Steps,
        Workflow,
        script,
    )
    from hera.workflows.artifact import ArtifactLoader
    from hera.workflows.volume import Volume


    @script(constructor="runner")
    def output_artifact(
        a_number: Annotated[int, Parameter(name="a_number")],
    ) -> Annotated[int, Artifact(name="successor_out")]:
        return a_number + 1


    @script(constructor="runner")
    def use_artifact(
        successor_in: Annotated[
            int,
            Artifact(
                name="successor_in",
                path="/tmp/file",
                loader=ArtifactLoader.json,
            ),
        ],
    ):
        print(successor_in)


    with Workflow(
        generate_name="test-output-annotations-",
        entrypoint="my-steps",
        volumes=[Volume(name="my-vol", size="1Gi")],
    ) as w:
        with Steps(name="my-steps") as s:
            out = output_artifact(arguments={"a_number": 3})
            use_artifact(arguments=[out.get_artifact("successor_out").with_name("successor_in")])
    ```

=== "YAML"

    ```yaml linenums="1"
    apiVersion: argoproj.io/v1alpha1
    kind: Workflow
    metadata:
      generateName: test-output-annotations-
    spec:
      entrypoint: my-steps
      templates:
      - name: my-steps
        steps:
        - - name: output-artifact
            template: output-artifact
            arguments:
              parameters:
              - name: a_number
                value: '3'
        - - name: use-artifact
            template: use-artifact
            arguments:
              artifacts:
              - name: successor_in
                from: '{{steps.output-artifact.outputs.artifacts.successor_out}}'
      - name: output-artifact
        inputs:
          parameters:
          - name: a_number
        outputs:
          artifacts:
          - name: successor_out
            path: /tmp/hera-outputs/artifacts/successor_out
        script:
          image: python:3.9
          source: '{{inputs.parameters}}'
          args:
          - -m
          - hera.workflows.runner
          - -e
          - examples.workflows.scripts.script_annotations_artifact_outputs_defaults:output_artifact
          command:
          - python
          env:
          - name: hera__outputs_directory
            value: /tmp/hera-outputs
      - name: use-artifact
        inputs:
          artifacts:
          - name: successor_in
            path: /tmp/file
        script:
          image: python:3.9
          source: '{{inputs.parameters}}'
          args:
          - -m
          - hera.workflows.runner
          - -e
          - examples.workflows.scripts.script_annotations_artifact_outputs_defaults:use_artifact
          command:
          - python
      volumeClaimTemplates:
      - metadata:
          name: my-vol
        spec:
          accessModes:
          - ReadWriteOnce
          resources:
            requests:
              storage: 1Gi
    ```

