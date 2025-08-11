import os
import json
import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from main import app  # type: ignore

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

def test_signals_default():
    r = client.get('/signals')
    assert r.status_code == 200
    assert isinstance(r.json(), list)

@pytest.mark.parametrize('strategy, symbols', [
    ('leveraged_etf', None),
    ('momentum_smallcap', 'AAPL,PLTR'),
])
def test_signals_strategies(strategy, symbols):
    params = {'strategy': strategy}
    if symbols:
        params['symbols'] = symbols
    r = client.get('/signals', params=params)
    assert r.status_code in (200, 400)
