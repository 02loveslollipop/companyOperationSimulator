# Cost Calculator JSON Structure Documentation

This document explains the structure of the `cost.json` file used by the cost calculator application to simulate income and expenses for a transportation company.

## Overview

The cost.json file contains structured data that defines:
- Costs associated with different aspects of the business (client-side, driver-side, backend)
- Global variables used across calculations
- Income sources for the business

The Python application uses this JSON structure to run simulations and calculate projected costs and income based on various input parameters.

## Top-Level Structure

```
{
    "cost": {
        // Cost categories and resources
    },
    "global": {
        // Global variables used in calculations
    },
    "income": {
        // Income sources and calculations
    }
}
```

## Cost Categories

The `cost` object contains three main categories:

1. `client` - Costs related to end-user app functionality
2. `driver` - Costs related to bus driver app functionality
3. `backend` - Costs related to server infrastructure and services

Each category contains:
- `description`: Text explaining the category
- `resource`: Array of resources/services that incur costs

## Resource Structure

Each resource within a category follows this structure:

```json
{
    "name": "Resource Name",
    "use_case": "Description of how this resource is used",
    "calculation_method": "Method used for billing (e.g., 'Requests per month')",
    "billing_method": "Detailed explanation of the billing structure",
    "unit": "Billing unit (e.g., 'USD')",
    "calculation_function": "formula" or {
        "preprocess": {
            "variable_name": "formula to calculate variable"
        },
        "cases": [
            {
                "case": "condition",
                "result": "formula for this case"
            }
        ]
    }
}
```

## Calculation Functions

The `calculation_function` field can be:
1. A direct formula (string) - Using global variables directly
2. A case-based object with conditions and corresponding formulas
3. A for-loop structure for iterative calculations
4. An exec block for executing a sequence of Python code statements

### Pre-processing in Calculations

All input transformation and preliminary calculations should be defined in the preprocess section:

```json
"calculation_function": {
    "preprocess": {
        "variable_name1": "formula1 using global variables",
        "variable_name2": "formula2 using global variables and previously defined variables"
    },
    "cases": [
        // cases using the preprocessed variables
    ]
}
```

The preprocessing step happens before any other calculation logic. Variables defined in the preprocess section can be used in subsequent calculations.

### Case-based Calculations

```json
"calculation_function": {
    "preprocess": {
        "processed_input": "global.users * global.rides_per_user"
    },
    "cases": [
        {
            "case": "processed_input <= 100000",
            "result": "formula if processed_input <= 100000"
        },
        {
            "case": "processed_input > 100000",
            "result": "formula if processed_input > 100000"
        }
    ]
}
```

### For-Loop Calculations

For calculations that require iteration or handling multiple items:

```json
"calculation_function": {
    "preprocess": {
        "iterations": "global.companies * global.average_requests_per_company"
    },
    "for": {
        "iterator": "iterations",
        "aggregation": "sum|average|max|min",
        "exec": [
            "statement1",
            "statement2",
            "result = formula"
        ]
    }
}
```

- `iterator`: Expression determining how many iterations to run
- `aggregation`: Method to combine results (sum, average, max, min)
- `exec`: Array of statements to execute in order for each iteration

### Exec Statements

Exec allows running multiple statements in sequence:

```json
"exec": [
    "variable1 = formula1",
    "variable2 = formula2",
    "result = final_formula"
]
```

The last statement should always assign to `result` which will be returned.

## Special Functions

The system provides several special functions that can be used in formulas:

### $random Function

Generates random values following a skewed distribution:

```
$random(min_value, max_value, mean_value)
```

- Used to simulate variability in inputs
- Internally uses the `SkewedRandomGenerator` class

## Global Variables

All variables used in calculations are defined in the `global` section:

```json
"global": {
    "users": 10000,
    "buses": 100,
    "rides_per_user": 2,
    "days_of_use": 30,
    // additional variables
}
```

### Accessing Global Variables

Global variables are accessed with the `global.` prefix:

```
"result": "global.users * global.price_per_ride"
```

### Common Global Variables

The system includes several predefined variables:

1. **User-related variables:**
   - `global.users`: Number of app users
   - `global.rides_per_user`: Average number of rides per user per day
   - `global.days_of_use`: Days of active usage per month
   - `global.user_recurrence`: Frequency of app checks during rides (minutes)

2. **Bus-related variables:**
   - `global.buses`: Number of buses in operation
   - `global.bus_operation_time`: Hours per day buses operate
   - `global.bus_route_update_recurrence`: Time between route updates (minutes)

3. **System variables:**
   - `global.month_from_startup`: Number of months since startup began
   - `global.averga_ride_time`: Average ride duration in minutes
   - `global.averga_route_calculation_time`: Average calculation time in seconds

4. **Business intelligence variables:**
   - `global.min_depth_of_query`: Minimum depth for microsegmentation queries
   - `global.max_depth_of_query`: Maximum depth for microsegmentation queries
   - `global.average_depth_of_query`: Average depth for microsegmentation queries
   - `global.companies`: Number of companies using microsegmentation data
   - `global.companies_growth_rate`: Monthly growth rate for company clients
   - `global.average_requests_per_company`: Average requests per company per month
   - `global.request_base_price`: Base price per request in USD

### Variable Scope and Lifetime

1. **Global variables** (`global.variable_name`):
   - Available throughout all calculations
   - Persist across all resource evaluations
   - Must be defined in the `global` section

2. **Preprocessed variables** (`variable_name`):
   - Available only within their specific calculation function
   - Created during the preprocessing phase of calculation
   - Don't persist beyond the current resource calculation

3. **For-loop variables**:
   - Available only within the execution block
   - Created fresh for each iteration
   - The `result` variable is aggregated according to the specified method

## Income Structure

The `income` section follows a similar structure to `cost`:

```json
"income": {
    "description": "Income description",
    "resource": [
        {
            "name": "Income Source Name",
            "use_case": "Description of how income is generated",
            "calculation_method": "Method used for billing",
            "billing_method": "Explanation of the billing structure",
            "unit": "USD",
            "calculation_function": {
                // Can be a direct formula, cases, for-loop
            }
        }
    ]
}
```

### Income Calculation Examples

Income can be calculated using various methods:

1. **Direct formula with preprocessing**:
   ```json
   "calculation_function": {
     "preprocess": {
       "ride_count": "global.users * global.rides_per_user"
     },
     "result": "ride_count * global.price_per_ride"
   }
   ```

2. **For-loop with random values**:
   ```json
   "calculation_function": {
     "preprocess": {
       "request_count": "global.companies * global.average_requests_per_company"
     },
     "for": {
       "iterator": "request_count",
       "aggregation": "sum",
       "exec": [
         "random = $random(global.min_depth_of_query, global.max_depth_of_query, global.average_depth_of_query)",
         "result = global.request_base_price * ((10^(-8) * random^2) + (0.00015 * random))"
       ]
     }
   }
   ```

## Calculation Processing Rules

When the Python application processes this JSON:

1. Global variables are first loaded from the `global` section
2. Each resource calculation proceeds as follows:
   - The `preprocess` section is evaluated first, creating local variables
   - Those variables are then used in subsequent calculations
   - For case-based functions, the appropriate case is selected based on conditions
   - For `for` loops, iterations are executed and results aggregated
   - For `exec` blocks, statements are executed in sequence
3. The final result is computed using the defined formula

## Usage in Python

The Python application reads this JSON structure and:
1. Loads all global variables into a context dictionary
2. For each resource:
   - Creates a local context with access to global variables
   - Executes preprocessing steps to transform inputs
   - Applies logic based on case conditions, loops, or direct formulas
   - Returns the final calculated value
3. Aggregates results across all resources and categories

## Example Simulation

For example, to simulate costs and income:
1. Define values for all required global variables in the `global` section
2. For each resource:
   - Execute preprocessing to transform inputs
   - Apply case logic or other calculation methods
   - Compute the final cost or income
3. Aggregate results across all resources and categories

## Using SkewedRandomGenerator for Simulations

The application includes a custom `SkewedRandomGenerator` class that can be used to generate random values following a skewed normal distribution. This is particularly useful for Monte Carlo simulations where you want to model uncertainty in inputs.

### Basic Usage

```python
from utils.SkewedRandomGenerator import SkewedRandomGenerator

# Create a generator with min=100, max=5000, mean=1000, and right skew
user_growth_generator = SkewedRandomGenerator(
    min_val=100,
    max_val=5000,
    target_mean=1000,
    skewness=3  # Positive for right skew
)

# Generate a random value
monthly_new_users = user_growth_generator.random()
```

### Applications in Cost Simulations

The random generator can be used to model:

1. **User Growth**:
   ```python
   # Example: Simulate user growth for 12 months
   global_vars["users"] = 1000
   for month in range(12):
       growth_rate = growth_rate_generator.random()  # Random growth rate
       global_vars["users"] += global_vars["users"] * growth_rate
       simulate_costs(global_vars)
   ```

2. **Usage Patterns**:
   ```python
   # Override global.rides_per_user with a random distribution
   global_vars["rides_per_user"] = daily_rides_generator.random()
   ```

3. **Monte Carlo Analysis**:
   ```python
   results = []
   for _ in range(1000):  # Run 1000 simulations
       global_vars["users"] = user_generator.random()
       global_vars["buses"] = bus_generator.random()
       result = simulate_costs(global_vars)
       results.append(result)
   ```

By incorporating the `SkewedRandomGenerator` through the `$random` function in the JSON configuration, you can create more realistic models that account for the uncertainty and variability inherent in business operations and user behavior.

## Using the CLI Tool

The cost calculator provides a command-line interface for generating reports and running simulations. Before using the tool, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Commands

The CLI tool provides two main commands:

1. **Generate a single cost report**:
```bash
python main.py single cost_clean.json [--variables NAME=VALUE...]

# Examples:
python main.py single cost_clean.json
python main.py single cost_clean.json --variables users=50000 buses=150
python main.py single cost_clean.json -v users=100000 -v buses=200 -v rides_per_user=3
```

The variables flag can override any global variable defined in the JSON file. Multiple variables can be set using multiple `-v` or `--variables` flags.

2. **Run a simulation over multiple periods**:
```bash
python main.py simulate cost_clean.json [--periods NUMBER]

# Examples:
python main.py simulate cost_clean.json
python main.py simulate cost_clean.json --periods 24
python main.py simulate cost_clean.json -p 36
```

The simulation will use the growth rates and increments defined in the JSON file's `global.variable` section to evolve the variables over time.

### Output Files

The tool generates two output files for each run:

1. **JSON Format** (`{input_file}_{type}_{timestamp}.json`):
   - Contains the full detailed report with all data
   - Useful for programmatic analysis or importing into other tools
   - Includes all global variables used in the calculation

2. **CSV Format** (`{input_file}_{type}_{timestamp}.csv`):
   - Human-readable tabular format
   - Easy to open in spreadsheet software
   - For simulations, includes a column for each period
   - Shows costs and income broken down by category and resource

The files are saved in the same directory as the input JSON file.

### Report Types

1. **Single Report** shows:
   - Total cost and breakdown by category/resource
   - Total income and breakdown by source
   - Net result (income - cost)
   - All global variables used in the calculation

2. **Simulation Report** shows:
   - Initial and final period summaries
   - Evolution of costs and income over time
   - Progress bar during simulation
   - Period-by-period breakdown in the CSV output

### Variables

You can override any global variable when generating a single report. The available variables are:

1. **User-related**:
   - `users`: Number of app users
   - `rides_per_user`: Average rides per user per day
   - `days_of_use`: Days of active usage per month
   - `user_recurrence`: App check frequency (minutes)

2. **Bus-related**:
   - `buses`: Number of buses
   - `bus_operation_time`: Daily operation hours
   - `bus_route_update_recurrence`: Route update interval

3. **System**:
   - `month_from_startup`: Months since launch
   - `averga_ride_time`: Average ride duration
   - `averga_route_calculation_time`: Route calculation time

4. **Business**:
   - `companies`: Number of data-buying companies
   - `request_base_price`: Base price per request
   - Other variables as defined in the JSON

All variables must be numeric values. The tool will attempt to convert input to floating-point numbers.