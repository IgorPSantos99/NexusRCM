"""Smoke tests for the initial NexusRCM package scaffold."""

from importlib import import_module

import pytest


def test_nexusrcm_package_imports() -> None:
    """Ensure the root package can be imported from the src layout."""
    package = import_module("nexusrcm")

    assert package is not None


@pytest.mark.parametrize(
    "module_name",
    [
        "nexusrcm.agent",
        "nexusrcm.api",
        "nexusrcm.graph",
        "nexusrcm.ingestion",
        "nexusrcm.nlp",
        "nexusrcm.retrieval",
    ],
)
def test_core_subpackages_import(module_name: str) -> None:
    """Ensure the initial package structure is importable."""
    module = import_module(module_name)

    assert module is not None
