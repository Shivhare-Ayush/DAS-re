"""tests/test_anchor_scrapers.py - Tests for Anchor Browser Telemetry Extraction."""
from agent.browser.scrapers import MockAnchorReconClient


def test_anchor_mock_scrape():
    client = MockAnchorReconClient()
    telemetry = client.scrape_dashboard("https://grafana.internal/d/auth")

    assert telemetry.service_name == "auth-gateway"
    assert telemetry.cpu_percent == 98.5
    assert telemetry.error_rate_percent == 94.2
    assert telemetry.active_connections == 4200
    assert len(telemetry.raw_metrics) == 2
