import logging
import os

def setup_logger(log_level_str='INFO', log_file='logs/app.log'):
    """
    Configures the root logger for the application.

    Args:
        log_level_str (str): The desired log level as a string (e.g., 'INFO', 'DEBUG').
        log_file (str): The path to the log file.

    Returns:
        logging.Logger: The configured root logger.
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            # Use basic print here since logger isn't fully set up
            print(f"Error creating log directory {log_dir}: {e}. Logging to current directory if possible.")
            # Fallback to a simpler log file name if directory creation fails
            log_file = os.path.basename(log_file) if os.path.basename(log_file) else 'app.log'


    # Get numeric log level
    numeric_level = getattr(logging, log_level_str.upper(), logging.INFO)
    if not isinstance(numeric_level, int): # Check if getattr returned a valid level
        print(f"Warning: Invalid log level string '{log_level_str}'. Defaulting to INFO.")
        numeric_level = logging.INFO
    
    # Define formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Get root logger
    # It's generally better to configure the root logger once if using basicConfig,
    # or get the root logger and add handlers if more control is needed or if basicConfig
    # might be called elsewhere. Since we are setting up handlers, let's get the root.
    
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers from the root logger to avoid duplicate logs if this function is called multiple times
    # (e.g., in tests or if re-initialized). This is a common practice.
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # File Handler
    try:
        fh = logging.FileHandler(log_file, mode='a') # 'a' for append
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)
    except IOError as e:
        print(f"Error: Could not open log file {log_file} for writing: {e}. File logging disabled.")


    # Stream Handler (console)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)

    # Test log to confirm setup
    # root_logger.info(f"Logger initialized with level {log_level_str} and file {log_file}")

    return root_logger # Return the root logger

if __name__ == '__main__':
    print("--- Testing Logger Setup ---")
    
    print("\n1. Default settings (INFO, logs/app.log):")
    logger1 = setup_logger()
    logger1.debug("This is a DEBUG message (should not appear by default).")
    logger1.info("This is an INFO message (default test).")
    logger1.warning("This is a WARNING message (default test).")

    print("\n2. Custom settings (DEBUG, logs/custom_debug.log):")
    # Ensure 'logs' dir exists for this test if it's cleaned up
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logger2 = setup_logger(log_level_str='DEBUG', log_file='logs/custom_debug.log')
    logger2.debug("This is a DEBUG message (custom test).")
    logger2.info("This is an INFO message (custom test).")

    print("\n3. Invalid log level (should default to INFO):")
    logger3 = setup_logger(log_level_str='INVALID_LEVEL', log_file='logs/invalid_level.log')
    logger3.debug("This is a DEBUG message (invalid level test - should not appear).")
    logger3.info("This is an INFO message (invalid level test - should appear).")

    # Test logging from a specific module logger after root setup
    print("\n4. Testing module-specific logger after root setup:")
    module_logger = logging.getLogger("MyModule")
    module_logger.info("This is an INFO message from MyModule.")
    module_logger.debug("This is a DEBUG message from MyModule (should appear if logger2 setup is active & DEBUG).")
    
    # If logger2 (DEBUG) is the last one configured, module_logger will inherit DEBUG level.
    # If basicConfig was used and called multiple times, behavior might be unexpected.
    # By getting root and clearing/adding handlers, we ensure more predictable behavior.

    print("\n--- Logger Setup Testing Complete ---")
    print("Check 'logs/app.log', 'logs/custom_debug.log', and 'logs/invalid_level.log' and console output.")
