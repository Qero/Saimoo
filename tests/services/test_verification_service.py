import pytest
from datetime import date
from unittest.mock import MagicMock
from saimoo.services.verification_service import VerificationService
from saimoo.utils.types import BarData, AdjustType

class TestVerificationService:
    @pytest.fixture
    def mock_storage(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_storage):
        return VerificationService(mock_storage)

    def test_verify_data_pass(self, service, mock_storage):
        # Setup identical data
        today = date.today()
        bar1 = BarData(symbol="600000", date=today, open=10.0, high=11.0, low=9.0, close=10.0, volume=1000, amount=10000)
        
        mock_storage.get_daily_bars.return_value = [bar1]
        
        result = service.verify_data("600000", today, today)
        
        assert result['status'] == "pass"
        # details might be empty string or None depending on implementation, here empty string joined from empty list
        assert result['details'] == ""
        mock_storage.save_verification_result.assert_called_once()

    def test_verify_data_fail(self, service, mock_storage):
        # Setup different data
        today = date.today()
        bar_ak = BarData(symbol="600000", date=today, open=10.0, high=11.0, low=9.0, close=10.0, volume=1000, amount=10000)
        bar_ts = BarData(symbol="600000", date=today, open=10.5, high=11.0, low=9.0, close=10.0, volume=1000, amount=10000)
        
        def get_bars(*args, **kwargs):
            if kwargs.get('source') == "akshare": return [bar_ak]
            return [bar_ts]
            
        mock_storage.get_daily_bars.side_effect = get_bars
        
        result = service.verify_data("600000", today, today)
        
        assert result['status'] == "fail"
        assert "open mismatch" in result['details']
        mock_storage.save_verification_result.assert_called_once()
