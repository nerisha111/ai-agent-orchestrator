#to ensure testing can occur in isolated, serverless or offline env

from unittest.mock import patch, MagicMock
from tools.enrich_company import enrich_company
from tools.get_lead_history import get_lead_history
from tools.update_crm_record import update_crm_record
from tools.create_support_ticket import create_support_ticket

def test_enrich_company_fallback():

    with patch("httpx.Client.get", side_effect=Exception("Timeout")):
        result = enrich_company(domain="stripe.com")
        assert result["fallback_applied"] is True
        assert result["domain"] == "stripe.com"
        assert result["registrar"] != "Unknown"

@patch("tools.get_lead_history.get_db_cursor")
def test_get_lead_history_not_found(mock_cursor):

    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_cursor.return_value.__enter__.return_value = mock_cur
    
    result = get_lead_history(email="test@notfound.com")
    assert result["found"] is False
    assert "No lead found" in result["message"]

@patch("tools.update_crm_record.get_db_cursor")
def test_update_crm_record_upsert(mock_cursor):
    import datetime
    
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [
        None, 
        {
            "id": 1, 
            "name": "Jane Doe", 
            "email": "jane@example.com", 
            "company": "JaneCorp", 
            "status": "new", 
            "source": "direct", 
            "updated_at": datetime.datetime.now()
        }
    ]
    mock_cursor.return_value.__enter__.return_value = mock_cur
    
    result = update_crm_record(email="jane@example.com", name="Jane Doe", company="JaneCorp")
    assert result["success"] is True
    assert result["record"]["name"] == "Jane Doe"