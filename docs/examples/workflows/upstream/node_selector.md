# Node Selector

## Note

This example is a replication of an Argo Workflow example in Hera.
The upstream example can be [found here](https://github.com/argoproj/argo-workflows/blob/main/examples/node-selector.yaml).




=== "Hera"

    ```python linenums="1"
    from hera.workflows import Container, Parameter, Workflow

    with Workflow(
        generate_name="node-selector-",
        entrypoint="print-arch",
        arguments=Parameter(name="arch", value="amd64"),
    ) as w:
        print_arch = Container(
            name="print-arch",
            inputs=[Parameter(name="arch")],
            image="alpine:latest",
            command=["sh", "-c"],
            args=["uname -a"],
            node_selector={"beta.kubernetes.io/arch": "{{inputs.parameters.arch}}"},
        )
    ```

=== "YAML"

    ```yaml linenums="1"
    apiVersion: argoproj.io/v1alpha1
    kind: Workflow
    metadata:
      generateName: node-selector-
    spec:
      entrypoint: print-arch
      templates:
      - name: print-arch
        container:
          image: alpine:latest
          args:
          - uname -a
          command:
          - sh
          - -c
        inputs:
          parameters:
          - name: arch
        nodeSelector:
          beta.kubernetes.io/arch: '{{inputs.parameters.arch}}'
      arguments:
        parameters:
        - name: arch
          value: amd64
    ```

