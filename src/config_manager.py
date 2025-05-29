import configparser
import os
import logging

logger = logging.getLogger(__name__)

def load_config(config_path='config/config.ini'):
    """
    Loads configuration from an INI file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: A dictionary containing configuration values, or None if an error occurs.
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file '{config_path}' not found.")
        return None

    config = configparser.ConfigParser()
    try:
        config.read(config_path)
    except configparser.Error as e:
        logger.error(f"Error reading configuration file '{config_path}': {e}", exc_info=True)
        return None

    config_values = {}

    # EXCHANGE section
    if 'EXCHANGE' not in config:
        logger.error(f"Missing [EXCHANGE] section in '{config_path}'.")
        return None

    try:
        config_values['api_key'] = config.get('EXCHANGE', 'API_KEY')
        config_values['api_secret'] = config.get('EXCHANGE', 'API_SECRET')
        config_values['default_exchange_id'] = config.get('EXCHANGE', 'DEFAULT_EXCHANGE_ID')
        config_values['use_testnet'] = config.getboolean('EXCHANGE', 'USE_TESTNET')
    except configparser.NoOptionError as e:
        logger.error(f"Missing option in [EXCHANGE] section of '{config_path}': {e}", exc_info=True)
        return None
    except ValueError as e: # For getboolean
        logger.error(f"Invalid boolean value for USE_TESTNET in [EXCHANGE] section of '{config_path}': {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading [EXCHANGE] section: {e}", exc_info=True)
        return None

    # Ensure essential keys are not empty
    if not config_values['api_key']:
        logger.error(f"API_KEY cannot be empty in '{config_path}'.")
        return None
    if not config_values['api_secret']:
        logger.error(f"API_SECRET cannot be empty in '{config_path}'.")
        return None
    if not config_values['default_exchange_id']:
        logger.error(f"DEFAULT_EXCHANGE_ID cannot be empty in '{config_path}'.")
        return None

    # GENERAL section (optional, with defaults)
    config_values['LOG_LEVEL'] = 'INFO' # Default
    config_values['LOG_FILE'] = 'logs/app.log' # Default

    if 'GENERAL' in config:
        try:
            log_level_from_config = config.get('GENERAL', 'LOG_LEVEL', fallback='INFO').strip()
            if log_level_from_config: 
                config_values['LOG_LEVEL'] = log_level_from_config
            
            log_file_from_config = config.get('GENERAL', 'LOG_FILE', fallback='logs/app.log').strip()
            if log_file_from_config:
                config_values['LOG_FILE'] = log_file_from_config

        except configparser.NoSectionError:
            logger.warning(f"[GENERAL] section defined but somehow not found during access in '{config_path}'. Using defaults for logging.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while reading [GENERAL] section: {e}. Using defaults for logging.", exc_info=True)
            config_values['LOG_LEVEL'] = 'INFO'
            config_values['LOG_FILE'] = 'logs/app.log'

    logger.debug(f"Configuration loaded from '{config_path}': {config_values}")
    return config_values

if __name__ == '__main__':
    # Setup basic logging for __main__ execution if needed
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Starting config_manager example...")

    if not os.path.exists('config'):
        os.makedirs('config')
    
    dummy_config_content = """
[EXCHANGE]
API_KEY = YOUR_TEST_API_KEY
API_SECRET = YOUR_TEST_API_SECRET
DEFAULT_EXCHANGE_ID = binance
USE_TESTNET = True

[GENERAL]
LOG_LEVEL = DEBUG
LOG_FILE = logs/custom_app.log
"""
    with open('config/config.ini', 'w') as f:
        f.write(dummy_config_content)

    logger.info("Attempting to load config/config.ini (with GENERAL section)...")
    config_data = load_config()
    if config_data:
        logger.info(f"Configuration loaded successfully: {config_data}")
    else:
        logger.error("Failed to load configuration.")

    dummy_config_no_general = """
[EXCHANGE]
API_KEY = test_key_no_general
API_SECRET = test_secret_no_general
DEFAULT_EXCHANGE_ID = kraken
USE_TESTNET = False
"""
    with open('config/no_general.ini', 'w') as f:
        f.write(dummy_config_no_general)
    logger.info("\nAttempting to load config/no_general.ini (no GENERAL section)...")
    config_no_general = load_config('config/no_general.ini')
    if config_no_general:
        logger.info(f"Configuration (no_general) loaded successfully: {config_no_general}")
        assert config_no_general.get('LOG_LEVEL') == 'INFO' 
        assert config_no_general.get('LOG_FILE') == 'logs/app.log' 
    else:
        logger.error("Failed to load configuration (no_general).")


    logger.info("\nAttempting to load non_existent_config.ini...")
    config_data_non_existent = load_config('non_existent_config.ini')
    if config_data_non_existent:
        logger.info("Configuration loaded successfully.")
    else:
        logger.error("Failed to load configuration as expected.")

    dummy_config_missing_section = """
[OTHER_SECTION]
SOME_KEY = SOME_VALUE
"""
    with open('config/missing_section.ini', 'w') as f:
        f.write(dummy_config_missing_section)
    logger.info("\nAttempting to load config/missing_section.ini (missing EXCHANGE section)...")
    config_data_missing_section = load_config('config/missing_section.ini')
    if not config_data_missing_section:
        logger.info("Failed to load configuration as expected due to missing section.")
    
    dummy_config_missing_key = """
[EXCHANGE]
API_KEY = testkey
# API_SECRET is missing
DEFAULT_EXCHANGE_ID = kraken
USE_TESTNET = False
"""
    with open('config/missing_key.ini', 'w') as f:
        f.write(dummy_config_missing_key)
    logger.info("\nAttempting to load config/missing_key.ini (missing API_SECRET)...")
    config_data_missing_key = load_config('config/missing_key.ini')
    if not config_data_missing_key:
        logger.info("Failed to load configuration as expected due to missing key.")

    dummy_config_invalid_bool = """
[EXCHANGE]
API_KEY = testkey
API_SECRET = testsecret
DEFAULT_EXCHANGE_ID = kraken
USE_TESTNET = Maybe
"""
    with open('config/invalid_bool.ini', 'w') as f:
        f.write(dummy_config_invalid_bool)
    logger.info("\nAttempting to load config/invalid_bool.ini (invalid USE_TESTNET)...")
    config_data_invalid_bool = load_config('config/invalid_bool.ini')
    if not config_data_invalid_bool:
        logger.info("Failed to load configuration as expected due to invalid boolean.")

    logger.info("\nCleaned up test config files.")
    # os.remove('config/config.ini') 
    os.remove('config/no_general.ini')
    os.remove('config/missing_section.ini')
    os.remove('config/missing_key.ini')
    os.remove('config/invalid_bool.ini')
    # if not os.listdir('config'):
    #     os.rmdir('config')
