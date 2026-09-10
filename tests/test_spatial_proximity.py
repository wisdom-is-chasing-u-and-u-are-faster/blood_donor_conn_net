"""
Test Suite for Real-Time Spatial Proximity & Geospatial Cache (ARCH-1188, ARCH-1189, ARCH-1190, ARCH-1191)
Tests Haversine distance, PostGIS bounding box filters, Redis GEOSEARCH, and rare phenotype matching.
"""
import pytest
import time
from services.spatial_service import (
    haversine_distance_km,
    get_bounding_box,
    RedisGeospatialCache
)


@pytest.fixture
def spatial_engine():
    cache = RedisGeospatialCache()
    # SF Memorial Hospital (Center: 37.7749, -122.4194)
    # Donor 1: 1.2 km away (O-Neg)
    cache.geoadd("donor-1", 37.7850, -122.4150, {
        "name": "Marcus Vance",
        "abo_type": "O",
        "rh_factor": "NEGATIVE",
        "rare_antigen_profile": {"kell": "negative", "duffy": "negative"}
    })
    # Donor 2: 6.5 km away (A-Pos)
    cache.geoadd("donor-2", 37.7300, -122.3800, {
        "name": "Jane Smith",
        "abo_type": "A",
        "rh_factor": "POSITIVE"
    })
    # Donor 3: 28 km away (O-Neg, Out of 15km radius)
    cache.geoadd("donor-3", 37.5500, -122.3000, {
        "name": "Out of Range Donor",
        "abo_type": "O",
        "rh_factor": "NEGATIVE"
    })
    return cache


def test_haversine_accuracy():
    # San Francisco to Oakland (~13 km)
    dist = haversine_distance_km(37.7749, -122.4194, 37.8044, -122.2712)
    assert 12.0 <= dist <= 15.0


def test_spatial_proximity_sweep_15km(spatial_engine):
    hosp_lat, hosp_lon = 37.7749, -122.4194
    start_t = time.perf_counter()
    candidates = spatial_engine.geosearch(hosp_lat, hosp_lon, radius_km=15.0)
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    # Sub-15ms check
    assert elapsed_ms < 15.0

    # Donor 1 and 2 within 15km; Donor 3 excluded
    candidate_ids = [c["member_id"] for c in candidates]
    assert "donor-1" in candidate_ids
    assert "donor-2" in candidate_ids
    assert "donor-3" not in candidate_ids


def test_rare_phenotype_and_blood_type_filtering(spatial_engine):
    hosp_lat, hosp_lon = 37.7749, -122.4194

    # Search specifically for O-Negative
    o_neg_candidates = spatial_engine.geosearch(
        hosp_lat, hosp_lon, radius_km=15.0,
        abo_type="O", rh_factor="NEGATIVE"
    )
    assert len(o_neg_candidates) == 1
    assert o_neg_candidates[0]["member_id"] == "donor-1"

    # Search for rare Kell negative
    kell_neg_candidates = spatial_engine.geosearch(
        hosp_lat, hosp_lon, radius_km=15.0,
        rare_antigen="kell"
    )
    assert len(kell_neg_candidates) == 1
    assert kell_neg_candidates[0]["member_id"] == "donor-1"
