import pytest
import pandas as pd
import os
import ccxt # For ccxt.NetworkError
from src.data_fetcher import DataFetcher
from tests.mocks import MockExchangeHandler # Import the mock
import logging # Add this import

@pytest.fixture
def mock_exchange_handler():
    return MockExchangeHandler()

@pytest.fixture
def data_fetcher(mock_exchange_handler):
    # Ensure that the mock exchange handler's exchange has markets loaded for some tests
    # This would typically be done by the ExchangeHandler's __init__ or a specific load_markets call
    mock_exchange_handler.load_markets()
    return DataFetcher(exchange_handler=mock_exchange_handler)

def test_data_fetcher_initialization(data_fetcher, mock_exchange_handler):
    assert data_fetcher.exchange_handler == mock_exchange_handler

def test_fetch_historical_ohlcv_success(data_fetcher, tmp_path, caplog):
    output_dir = str(tmp_path)
    symbol = "BTC/USDT" # Using a symbol defined in MockCCXTExchange.load_markets
    df = data_fetcher.fetch_historical_ohlcv(symbol=symbol, timeframe='1h', limit=1, output_dir=output_dir)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])

    # Check if file was created
    # MockExchangeHandler uses 'mock_exchange' as id by default
    # _make_safe_filename converts 'BTC/USDT' to 'BTC_USDT'
    expected_filename = "mock_exchange_BTC_USDT_1h.csv"
    file_path = os.path.join(output_dir, expected_filename)
    assert os.path.exists(file_path), f"File not found: {file_path}"
    # Verify content if necessary by reading the CSV
    df_read = pd.read_csv(file_path)
    assert len(df_read) == 1
    assert df_read['open'].iloc[0] == 16000 # From mock OHLCV data

def test_filename_sanitization_in_fetch(data_fetcher, tmp_path):
    output_dir = str(tmp_path)
    symbol = "ETH/USDT:USDT" # Symbol with special characters
    # This symbol is defined in MockCCXTExchange.load_markets as a future
    data_fetcher.fetch_historical_ohlcv(symbol=symbol, timeframe='1d', limit=1, output_dir=output_dir)
    
    expected_filename = "mock_exchange_ETH_USDT_USDT_1d.csv"
    file_path = os.path.join(output_dir, expected_filename)
    assert os.path.exists(file_path), f"File not found: {file_path}"

def test_fetch_historical_ohlcv_api_error(data_fetcher, mock_exchange_handler, caplog, tmp_path):
    original_fetch_ohlcv = mock_exchange_handler.exchange.fetch_ohlcv
    
    def mock_fetch_ohlcv_error(*args, **kwargs):
        raise ccxt.NetworkError("Simulated API error")
    
    mock_exchange_handler.exchange.fetch_ohlcv = mock_fetch_ohlcv_error
    
    df = data_fetcher.fetch_historical_ohlcv(symbol="ERROR/SYMBOL", output_dir=str(tmp_path))
    
    assert df is None 
    # Check for log messages from data_fetcher.py
    assert "Network error fetching OHLCV for ERROR/SYMBOL" in caplog.text 
    assert "Simulated API error" in caplog.text

    # Restore original method to avoid affecting other tests
    mock_exchange_handler.exchange.fetch_ohlcv = original_fetch_ohlcv

def test_fetch_historical_ohlcv_no_data_returned(data_fetcher, mock_exchange_handler, tmp_path, caplog):
    caplog.set_level(logging.INFO) # Set capture level for this test
    original_fetch_ohlcv = mock_exchange_handler.exchange.fetch_ohlcv
    
    def mock_fetch_empty_ohlcv(*args, **kwargs):
        return [] # Simulate exchange returning empty list
        
    mock_exchange_handler.exchange.fetch_ohlcv = mock_fetch_empty_ohlcv
    
    symbol = "EMPTY/DATA"
    df = data_fetcher.fetch_historical_ohlcv(symbol=symbol, output_dir=str(tmp_path))
    
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert f"No data returned by exchange for {symbol}" in caplog.text
    
    # Check that an empty CSV file is still created (as per current DataFetcher logic)
    # expected_filename = f"mock_exchange_{symbol.replace('/', '_')}_1h.csv"
    # file_path = os.path.join(tmp_path, expected_filename)
    # assert os.path.exists(file_path) # Current DataFetcher creates empty file

    mock_exchange_handler.exchange.fetch_ohlcv = original_fetch_ohlcv

def test_fetch_ohlcv_output_dir_none(data_fetcher, tmp_path, caplog):
    caplog.set_level(logging.INFO) # Set capture level for this test
    # tmp_path is used here just to ensure the test runs in a clean environment,
    # but no file should be created in it or anywhere else.
    symbol = "BTC/USDT"
    df = data_fetcher.fetch_historical_ohlcv(symbol=symbol, timeframe='1h', limit=1, output_dir=None)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "output_dir is None, skipping CSV saving." in caplog.text

    # Check that NO file was created
    # Construct a potential filename and ensure it does NOT exist
    potential_filename = "mock_exchange_BTC_USDT_1h.csv"
    file_path_in_tmp = tmp_path / potential_filename
    current_dir_file_path = "./" + potential_filename # Check current dir too
    
    assert not os.path.exists(file_path_in_tmp), f"File was unexpectedly created in tmp_path: {file_path_in_tmp}"
    assert not os.path.exists(current_dir_file_path), f"File was unexpectedly created in current dir: {current_dir_file_path}"
