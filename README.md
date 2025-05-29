# AI-Powered Futures Trading Bot

## Description
A Python-based bot designed for automated futures trading on designated cryptocurrency exchanges. This project aims to integrate AI/ML models for generating trading signals, executing trades, and managing risk.

## Current Status
Initial framework development is complete. Core modules for configuration, exchange interaction, data fetching, basic signal generation, mock trading execution, a command-line interface (CLI), logging, and initial unit tests are in place. The bot is currently suitable for development and testing, primarily on exchange testnets.

## Core Modules & Features
- **Configuration Management**: Securely loads settings like API keys and logging preferences from `config/config.ini`. (See `src/config_manager.py`)
- **Exchange Handler**: Connects to exchanges via CCXT for operations like fetching balance and market data. (See `src/exchange_handler.py`)
- **Data Fetcher**: Downloads historical OHLCV (Open, High, Low, Close, Volume) data and saves it to CSV. (See `src/data_fetcher.py`)
- **Signal Generation**: A modular system to integrate AI/ML models. Includes basic `RandomSignalGenerator` and `MovingAverageCrossoverSignalGenerator`. (See `src/models/signal_generator.py`)
- **Trading Engine**: Executes trades (currently market orders) based on generated signals. (See `src/trading_engine.py`)
- **Command-Line Interface (CLI)**: Allows interaction with the bot's functionalities via `main.py`.
- **Logging**: Comprehensive logging of activities and errors, configurable via `config.ini`. (See `src/logger_setup.py`, logs stored in `logs/`)
- **Unit Tests**: Basic unit tests using `pytest` to ensure core component reliability. (See `tests/`)

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <project-directory>
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    ```
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    -   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up configuration:**
    -   Copy the example configuration file:
        ```bash
        cp config/config.example.ini config/config.ini
        ```
    -   Edit `config/config.ini` with your exchange API keys (preferably use testnet keys for initial setup and testing) and other preferences like default exchange or log level.

## Basic Usage Instructions (CLI)

Ensure your `config/config.ini` is correctly set up and your virtual environment is activated.

-   **Get account balance:**
    ```bash
    python main.py get-balance
    ```

-   **Fetch historical OHLCV data:**
    ```bash
    python main.py fetch-ohlcv --symbol BTC/USDT:USDT --timeframe 1h --limit 100
    ```
    *(Symbol format might vary by exchange; use formats recognized by CCXT for your target exchange, especially for futures contracts like `BTC/USDT:USDT` for USDT-margined Bitcoin perpetuals on Binance).*

-   **Get a trading signal (default: Moving Average Crossover):**
    ```bash
    python main.py get-signal --symbol BTC/USDT:USDT
    ```

-   **Get a random trading signal:**
    ```bash
    python main.py get-signal --symbol BTC/USDT:USDT --model random
    ```

-   **Simulate executing a trade:**
    *(Ensure you are using testnet credentials or understand the risk if using live funds.)*
    ```bash
    python main.py execute-trade --symbol BTC/USDT:USDT --signal BUY --quantity 0.001
    ```

## Running Tests

-   To run all unit tests:
    ```bash
    pytest
    ```
-   For more verbose output:
    ```bash
    pytest -v
    ```

## Future Development
-   Integration of more sophisticated AI/ML models (e.g., LSTMs, Reinforcement Learning).
-   Real-time data stream processing via WebSockets.
-   Advanced risk management features (stop-loss, take-profit, position sizing).
-   Development of a Graphical User Interface (Web or Desktop).
-   Robust backtesting module with performance analytics.
-   Paper trading mode against live exchange data.
```
