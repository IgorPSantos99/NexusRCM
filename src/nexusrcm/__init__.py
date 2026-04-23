"""NexusRCM source package."""

from nexusrcm.interfaces import (
    BaseExtractor,
    BaseLoader,
    BaseRetriever,
    BaseVectorStore,
    DiagnosticAgent,
    GraphStore,
)

__all__ = [
    "BaseExtractor",
    "BaseLoader",
    "BaseRetriever",
    "BaseVectorStore",
    "DiagnosticAgent",
    "GraphStore",
]

"""
NOTE: In many projects, this file is left empty and only marks the directory
as a Python package. In NexusRCM, it is also used to define the package's
public API by re-exporting the central symbols that other modules should
import directly from `nexusrcm`.

This makes the package easier to consume and signals which abstractions are
considered stable and core to the architecture.

To preserve readability, only truly central objects should be exported here,
such as interfaces, schemas, and settings.
"""
