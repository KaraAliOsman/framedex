from dekopen_engine import PACKAGE_NAME, __version__


def test_engine_package_contract() -> None:
    assert PACKAGE_NAME == "dekopen-engine"
    assert __version__ == "0.1.0"
