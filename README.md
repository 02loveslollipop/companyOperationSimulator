# Cost Calculator

> A simulator for modeling and reporting operational costs and income based on a JSON configuration, featuring both CLI and Streamlit interfaces.

## Intro

This tool simulates and reports operational costs and income for businesses, particularly useful for modeling scenarios like transportation companies. It uses a structured JSON configuration (`input.json`) to define business logic, cost/income resources, and simulation parameters, including growth models and randomization. The tool provides both a Command-Line Interface (CLI) for batch processing and report generation, and an interactive Streamlit web dashboard for visual analysis and parameter tuning.

## Project Structure (Example)

*   `app.py`: Main Streamlit dashboard application script.
*   `cli.py`: Command-Line Interface script.
*   `pkg/`: Directory containing the core simulation and calculation logic (e.g., `calculator.py`, `models.py`, `utils/`).
*   `input.json`: Example input configuration file defining the business model.
*   `requirements.txt`: Python dependencies required to run the tool.
*   `README.md`: This file.
*   `companyOperationSimulator.wiki/`: Directory containing detailed documentation (Wiki pages).

## Getting Started

### Prerequisites

*   Python 3.8+
*   pip (Python package installer)

### 1. Installation

Clone the repository (if applicable) and install the required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Running the Tool

You can interact with the simulator using either the CLI or the Streamlit Dashboard.

**a) Using the CLI (`cli.py`)**

The CLI is useful for generating reports programmatically or as part of automated workflows.

1.  **Generate a single-period report:**
    Calculates results based on initial values (optionally overridden).

    ```bash
    python cli.py single <your-input-file>.json [--variables NAME=VALUE...]
    ```
    *Example:*
    ```bash
    python cli.py single input.json -v users=5000 -v companies=15
    ```

2.  **Run a multi-period simulation:**
    Calculates results over time, applying growth models.

    ```bash
    python cli.py simulate <your-input-file>.json [--periods NUMBER]
    ```
    *Example:*
    ```bash
    python cli.py simulate input.json -p 24 # Simulate for 24 periods
    ```

See [[CLI Usage|CLI-Usage]] for more details. Output files are generated as described in [[Output Files|Output-Files]].

**b) Using the Streamlit Dashboard (`app.py`)**

The dashboard provides an interactive way to explore the simulation.

1.  **Run the dashboard:**
    ```bash
    streamlit run app.py
    ```
2.  **Interact:**
    *   Upload your `input.json` file.
    *   Adjust global variable overrides in the sidebar.
    *   Set the number of forecast periods.
    *   Run the calculation/simulation.
    *   Explore the results, plots, detailed tables, and logs.

See [[Streamlit Dashboard|Streamlit-Dashboard]] for a full feature list.

## Features Overview

*   **JSON Configuration**: Define models, costs, income via a structured JSON. ([[JSON Structure|json-structure]])
*   **Simulation Engine**: Model growth over time using linear/polynomical/logistic rates or increments. ([[Global Variables|global-variables]])
*   **Randomization**: Use `$random(min, max, mean)` for Monte Carlo analysis. ([[Randomization and Simulation|Randomization-and-Simulation]])
*   **Flexible Calculations**: Define resource values using direct formulas, conditional cases, preprocessing steps, or loops. ([[Calculation Functions|calculation-functions]], [[Expression Language|Expression-Language]])
*   **CLI & Streamlit Interfaces**: Choose between command-line or interactive web UI. ([[CLI Usage|CLI-Usage]], [[Streamlit Dashboard|Streamlit-Dashboard]])
*   **Detailed Reporting**: Get results in JSON/CSV formats and view calculation logs. ([[Output Files|Output-Files]], [[Streamlit Dashboard|Streamlit-Dashboard]])
*   **Error Handling**: Guidance on common errors and best practices. ([[Error Handling and Best Practices|Error-Handling-and-Best-Practices]])

## Documentation

Detailed documentation is available in the project's Wiki: [[Home]]