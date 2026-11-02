import pytest
from app import app
from blueprints.dashboard_donors import mask_contact, mask_donor_id, COMPATIBILITY_MATRIX


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_compatibility_matrix_rules():
    """Verify standard ABO/Rh blood group compatibility rules (REQ-F-012)."""
    # O- is universal donor (compatible with all 8 groups)
    for bg, compatible_donors in COMPATIBILITY_MATRIX.items():
        assert "O-" in compatible_donors, f"O- should be compatible with recipient {bg}"

    # AB+ is universal recipient (can receive from all 8 groups)
    assert len(COMPATIBILITY_MATRIX["AB+"]) == 8

    # O- can only receive from O-
    assert COMPATIBILITY_MATRIX["O-"] == ["O-"]

    # A+ can receive from A+, A-, O+, O-
    assert set(COMPATIBILITY_MATRIX["A+"]) == {"A+", "A-", "O+", "O-"}


def test_contact_masking():
    """Verify contact details masking by default (REQ-F-018)."""
    masked = mask_contact("(555) 234-5544", user_role="hospital")
    assert masked == "(***) ***-5544"

    # Emergency authorized role sees unmasked
    unmasked = mask_contact("(555) 234-5544", user_role="emergency_authorized")
    assert unmasked == "(555) 234-5544"

    # Donor ID masking
    assert mask_donor_id("BDC-101-0112") == "BDC-***-0112"


def test_dashboard_donors_filter_endpoint_a_positive(client):
    """Test GET /api/v1/dashboard/donors/filter for A+ recipient with verified_only=true (REQ-F-020, REQ-F-011)."""
    response = client.get(
        "/api/v1/dashboard/donors/filter?blood_group=A+&verified_only=true")
    assert response.status_code == 200
    data = response.get_json()

    assert "kpis" in data
    kpis = data["kpis"]
    assert kpis["total_compatible"] > 0
    assert kpis["exact_matches"] > 0
    assert kpis["universal_donor_standby"] >= 1

    donors = data["donors"]
    assert len(donors) > 0
    for d in donors:
        assert d["blood_group"] in ["A+", "A-", "O+", "O-"]
        assert d["status"] == "Verified"
        assert "(***) ***-" in d["masked_contact"]
        assert "BDC-***-" in d["donor_id"]


def test_dashboard_donors_filter_endpoint_unverified_included(client):
    """Test filter with verified_only=false includes pending donors."""
    response = client.get(
        "/api/v1/dashboard/donors/filter?blood_group=A+&verified_only=false")
    assert response.status_code == 200
    data = response.get_json()
    donors = data["donors"]
    # Emma Stone is unverified A+ donor in default seed
    statuses = [d["status"] for d in donors]
    assert "Pending" in statuses


def test_hospital_compatibility_dashboard_page_render(client):
    """Test GET /hospital/compatibility-dashboard renders with KPI cards and filters."""
    response = client.get("/hospital/compatibility-dashboard")
    assert response.status_code == 200
    assert b"Hospital Compatibility Dashboard" in response.data
    assert b"Recipient Blood Group" in response.data
    assert b"kpi-total-compatible" in response.data
    assert b"donors-table" in response.data


def test_health_check(client):
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
