"""Foundation tests for the NEXUS package."""

from nexus import __version__


def test_package_version_is_defined() -> None:
    """The package exposes an initial version."""
    assert __version__ == "0.1.0"
