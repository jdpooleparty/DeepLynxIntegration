import pytest
from src.core.deep_lynx import DeepLynxClient

def test_deep_lynx_client_initialization():
    client = DeepLynxClient()
    assert client is not None
    assert client.settings is not None
