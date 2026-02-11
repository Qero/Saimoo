# Saimoo

A Quant Investment Tool for China A-Shares.

## Features

- **Data**: Market data ingestion, cleaning, and storage.
- **Research**: Factor analysis, feature engineering.
- **Strategy**: Flexible strategy framework (Backtest & Live).
- **Execution**: Order management and risk control.

## Getting Started

### Prerequisites

- Python 3.10+
- uv (Dependency Management)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

### Usage

Run the CLI:
```bash
uv run python -m saimoo.cli.main --help
```

### Development

Run tests:
```bash
uv run pytest
```
