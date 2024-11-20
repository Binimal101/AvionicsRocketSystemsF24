import pytest
from unittest.mock import MagicMock, patch
from main import FlightDataLogger  # Import from main.py where FlightDataLogger is defined

@pytest.fixture
def flight_data_logger():
    """Fixture to create an instance of FlightDataLogger with a mocked sensor."""
    with patch('main.board') as mock_board:
        # Mock the I2C interface and the sensor
        mock_sensor = MagicMock()
        mock_board.I2C.return_value = mock_sensor
        logger = FlightDataLogger()
        logger.sensor = mock_sensor  # Assign the mocked sensor to avoid hardware dependency
        return logger

@pytest.mark.parametrize("temperature, last_temperature, expected", [
    (25, 25, 25),  # Normal case: same temperature
    (25, 0xFFFF, 25),  # Normal case: first reading
    (25, 153, 25),  # Normal case: new reading
    (153, 25, 153),  # Normal case: new reading
    (153, 153 + 128, 0b00111111 & 153),  # Edge case: roll-over correction
    (0b00111111 & 153, 153 + 128, 0b00111111 & (153 + 128)),  # Edge case: re-read
])
def test_get_temperature_positive(flight_data_logger, temperature, last_temperature, expected):
    """Test get_temperature for various scenarios to ensure it returns expected values."""
    flight_data_logger.sensor.temperature = temperature
    flight_data_logger.last_temperature_reading = last_temperature
    
    result = flight_data_logger.get_temperature()
    
    assert result == expected

@pytest.mark.parametrize("temperature", [
    (0xFFFF),  # Edge case: erroneous high temperature
    (0),  # Edge case: erroneous low temperature
    (0b11111111),  # Random high value
])

def test_get_temperature_negative(flight_data_logger, temperature):
    """Test get_temperature for erroneous cases to ensure it handles unexpected readings."""
    flight_data_logger.sensor.temperature = temperature
    flight_data_logger.last_temperature_reading = 153  # Example previous reading

    # Invoke get_temperature and check if the returned value is not equal to temperature
    result = flight_data_logger.get_temperature()
    
    assert result != temperature
