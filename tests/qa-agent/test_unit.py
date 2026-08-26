"""
QA Persona v2 -- auto-generated tests
Service: cloned_repo
Suite:   unit
Source:  test_strategy/plans/cloned_repo__unit.json
Generated: 2024-07-25T19:57:04.289350
"""

import pytest
import io
from unittest.mock import patch, MagicMock

from app import app, admin_audit_log, verify_demand, create_demand

def test_admin_audit_log_retrieves_log_data():
    """Verify admin_audit_log function retrieves log data.

    test_id: cloned_repo__unit__001
    target: admin_audit_log
    requirement_id: REQ-N-012, REQ-N-011
    ac_ids: REQ-N-012-AC-1, REQ-N-011-AC-1
    """
    mock_logs = [{"timestamp": "2023-01-01 10:00:00", "detail": "log1"}]
    
    with app.test_request_context('/admin/audit-log'):
        with patch('app.session', {'role': 'admin'}):
            with patch('app.audit_logs', mock_logs):
                with patch('app.render_template') as mock_render_template:
                    mock_render_template.return_value = "<html></html>"
                    
                    admin_audit_log()

                    sorted_mock_logs = sorted(mock_logs, key=lambda x: x["timestamp"], reverse=True)
                    mock_render_template.assert_called_once_with("audit_log.html", logs=sorted_mock_logs)

def test_verify_demand_triggers_event_publication():
    """Verify verify_demand function triggers event publication.

    test_id: cloned_repo__unit__002
    target: verify_demand
    requirement_id: REQ-F-017
    ac_ids: REQ-F-017-AC-1
    """
    mock_demands = [{
        "id": 1,
        "hospital": "Test Hospital",
        "blood_type": "A+",
        "units": 5,
        "status": "Pending"
    }]
    mock_alerts = []
    mock_audit_logs = []

    with app.test_request_context('/admin/verify/1', method='POST', data={'action': 'approve'}):
        with patch('app.session', {'role': 'admin', 'username': 'test_admin'}):
            with patch('app.demands', mock_demands):
                with patch('app.alerts', mock_alerts):
                    with patch('app.audit_logs', mock_audit_logs):
                        with patch('app.flash'):
                            verify_demand(demand_id=1)

                            assert mock_demands[0]['status'] == 'Approved'
                            
                            assert len(mock_alerts) == 1
                            assert mock_alerts[0]['hospital'] == 'Test Hospital'
                            
                            assert len(mock_audit_logs) == 1
                            assert mock_audit_logs[0]['action'] == 'EMERGENCY DEMAND APPROVED'
                            assert "Emitted event" in mock_audit_logs[0]['details']

def test_create_demand_processes_valid_payload():
    """Verify create_demand function processes valid payload.

    test_id: cloned_repo__unit__003
    target: create_demand
    requirement_id: REQ-N-007
    ac_ids: REQ-N-007-AC-1
    """
    mock_demands = []
    mock_audit_logs = []
    
    form_data = {
        'blood_type': 'B+',
        'units': '3',
        'notes': 'Urgent need'
    }
    file_data = {
        'document': (io.BytesIO(b'some file data'), 'test_doc.pdf')
    }
    request_data = {**form_data, **file_data}

    with app.test_request_context('/hospital/create-demand', method='POST', data=request_data, content_type='multipart/form-data'):
        with patch('app.session', {'role': 'hospital', 'username': 'test_hospital'}):
            with patch('app.demands', mock_demands):
                with patch('app.audit_logs', mock_audit_logs):
                    with patch('app.flash'):
                        create_demand()

                        assert len(mock_demands) == 1
                        new_demand = mock_demands[0]
                        assert new_demand['blood_type'] == 'B+'
                        assert new_demand['units'] == 3
                        assert new_demand['filename'] == 'test_doc.pdf'
                        assert new_demand['status'] == 'Pending'
                        assert new_demand['hospital'] == 'test_hospital'

                        assert len(mock_audit_logs) == 1
                        new_log = mock_audit_logs[0]
                        assert new_log['action'] == 'BLOOD DEMAND CREATED'
                        assert 'test_doc.pdf' in new_log['details']
