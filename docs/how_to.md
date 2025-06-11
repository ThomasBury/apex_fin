# How-To Guide: Using the CLI

This guide explains how to use the command-line interface (CLI) for the `apex-fin` application to generate financial analysis reports.

The CLI is powered by `typer` and provides several commands for different types of analysis.

## Available Commands

All commands support the following optional flags:

* `--config <path>` or `-c <path>`: Specify a custom YAML configuration file to override default settings.
* `--output <path>` or `-o <path>`: Write the report output to a specified Markdown file instead of printing to the console.

Here are the main commands:

### `analyze <ticker>`

Runs a financial health analysis for a single company.

* **`<ticker>`**: The stock ticker symbol (e.g., `AAPL`, `MSFT`).

**Example:**

```bash
uv run python -m apex_fin.main analyze AAPL
```

### `compare <ticker>`

Compares a company to its top competitors.

* **`<ticker>`**: The stock ticker symbol of the primary company to compare (e.g., `GOOGL`, `TSLA`).

**Example:**

```bash
uv run python -m apex_fin.main compare MSFT
```

### `think <ticker>`

Performs contextual reasoning and policy checks for a stock, focusing on macroeconomic and geopolitical risks.

* **`<ticker>`**: The stock ticker symbol for which to perform contextual reasoning (e.g., `NVDA`, `VZ`).

**Example:**

```bash
uv run python -m apex_fin.main think GOOGL
```

### `fullreport <ticker>`

Generates a complete financial report for a stock, combining multiple analysis sections.

* **`<ticker>`**: The stock ticker symbol for which to generate a full report (e.g., `JPM`, `XOM`).

**Example:**

```bash
uv run python -m apex_fin.main fullreport AMZN
```

**Example with output to file:**

```bash
uv run python -m apex_fin.main fullreport TSLA --output tsla_report.md
```

This guide covers the basic usage of the `apex-fin` CLI commands. Refer to the API Reference for more detailed information on the underlying modules and functions.
