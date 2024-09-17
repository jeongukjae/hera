# generated by datamodel-codegen:
#   filename:  argo-workflows-3.5.5.json

from __future__ import annotations

from typing import Annotated, Optional

from hera.shared._pydantic import BaseModel, Field

from ...apimachinery.pkg.apis.meta import v1
from ...apimachinery.pkg.util import intstr


class PodDisruptionBudgetSpec(BaseModel):
    max_unavailable: Annotated[
        Optional[intstr.IntOrString],
        Field(
            alias="maxUnavailable",
            description=(
                'An eviction is allowed if at most "maxUnavailable" pods selected by'
                ' "selector" are unavailable after the eviction, i.e. even in absence'
                " of the evicted pod. For example, one can prevent all voluntary"
                " evictions by specifying 0. This is a mutually exclusive setting with"
                ' "minAvailable".'
            ),
        ),
    ] = None
    min_available: Annotated[
        Optional[intstr.IntOrString],
        Field(
            alias="minAvailable",
            description=(
                'An eviction is allowed if at least "minAvailable" pods selected by'
                ' "selector" will still be available after the eviction, i.e. even in'
                " the absence of the evicted pod.  So for example you can prevent all"
                ' voluntary evictions by specifying "100%".'
            ),
        ),
    ] = None
    selector: Annotated[
        Optional[v1.LabelSelector],
        Field(
            description=(
                "Label query over pods whose evictions are managed by the disruption"
                " budget. A null selector will match no pods, while an empty ({})"
                " selector will select all pods within the namespace."
            )
        ),
    ] = None
