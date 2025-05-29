import pytest
import os
import configparser
from src.config_manager import load_config

@pytest.fixture
def temp_config_file(tmp_path):
    config_content = """
[EXCHANGE]
API_KEY = TEST_KEY
API_SECRET = TEST_SECRET
DEFAULT_EXCHANGE_ID = test_exchange
USE_TESTNET = True

[GENERAL]
LOG_LEVEL = DEBUG
LOG_FILE = logs/test.log
"""
    p = tmp_path / "test_config.ini"
    p.write_text(config_content)
    return str(p)

def test_load_config_success(temp_config_file):
    config = load_config(temp_config_file)
    assert config is not None
    assert config['api_key'] == 'TEST_KEY'
    assert config['api_secret'] == 'TEST_SECRET'
    assert config['default_exchange_id'] == 'test_exchange'
    assert config['use_testnet'] is True
    assert config['LOG_LEVEL'] == 'DEBUG'
    assert config['LOG_FILE'] == 'logs/test.log'

def test_load_config_file_not_found(caplog):
    config = load_config("non_existent_config.ini")
    assert config is None
    assert "Configuration file 'non_existent_config.ini' not found." in caplog.text

def test_load_config_missing_section(tmp_path, caplog):
    p = tmp_path / "missing_section.ini"
    p.write_text("""
[OTHER_SECTION]
key=value
""")
    config = load_config(str(p))
    assert config is None 
    assert "Missing [EXCHANGE] section in" in caplog.text # Adjusted for actual log message

def test_load_config_missing_key(tmp_path, caplog):
    p = tmp_path / "missing_key.ini"
    p.write_text("""
[EXCHANGE]
API_KEY=ONLY_ONE_KEY
DEFAULT_EXCHANGE_ID = test_exchange
USE_TESTNET = True
""")
    config = load_config(str(p))
    assert config is None
    assert "Missing option in [EXCHANGE] section" in caplog.text # Adjusted
    assert "No option 'api_secret' in section: 'EXCHANGE'" in caplog.text # More specific part of the actual log

def test_load_config_empty_values(tmp_path, caplog):
    p = tmp_path / "empty_values.ini"
    p.write_text("""
[EXCHANGE]
API_KEY =
API_SECRET = TEST_SECRET
DEFAULT_EXCHANGE_ID = test_exchange
USE_TESTNET = True
""")
    config = load_config(str(p))
    assert config is None
    assert "API_KEY cannot be empty" in caplog.text # Adjusted

def test_load_config_invalid_boolean(tmp_path, caplog):
    p = tmp_path / "invalid_boolean.ini"
    p.write_text("""
[EXCHANGE]
API_KEY = TEST_KEY
API_SECRET = TEST_SECRET
DEFAULT_EXCHANGE_ID = test_exchange
USE_TESTNET = NOT_A_BOOLEAN
""")
    config = load_config(str(p))
    assert config is None
    assert "Invalid boolean value for USE_TESTNET" in caplog.text # Adjusted
    assert "Not a boolean: NOT_A_BOOLEAN" in caplog.text # More specific part of the actual log

def test_load_config_general_section_defaults(tmp_path):
    config_content = """
[EXCHANGE]
API_KEY = TEST_KEY_NO_GENERAL
API_SECRET = TEST_SECRET_NO_GENERAL
DEFAULT_EXCHANGE_ID = test_exchange_no_general
USE_TESTNET = False
"""
    p = tmp_path / "no_general_config.ini"
    p.write_text(config_content)
    config = load_config(str(p))
    assert config is not None
    assert config['LOG_LEVEL'] == 'INFO' # Default value
    assert config['LOG_FILE'] == 'logs/app.log' # Default value

def test_load_config_general_section_partial(tmp_path):
    config_content = """
[EXCHANGE]
API_KEY = TEST_KEY_PARTIAL
API_SECRET = TEST_SECRET_PARTIAL
DEFAULT_EXCHANGE_ID = test_exchange_partial
USE_TESTNET = False

[GENERAL]
LOG_LEVEL = WARNING
""" # LOG_FILE is missing, should use default
    p = tmp_path / "partial_general_config.ini"
    p.write_text(config_content)
    config = load_config(str(p))
    assert config is not None
    assert config['LOG_LEVEL'] == 'WARNING'
    assert config['LOG_FILE'] == 'logs/app.log' # Default value
