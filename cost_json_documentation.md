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

A `category` is a high-level grouping of related resources that incur costs or generate income. Each category has a `description` and a list of `resource` objects that detail the specific costs or income sources from that category.

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
         "result = global.request_base_price * ((10**(-8) * random**2) + (0.00015 * random))"
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
python main.py single <your-file-name>.json [--variables NAME=VALUE...]

# Examples:
python main.py single <your-file-name>.json
python main.py single <your-file-name>.json --variables users=50000 buses=150
python main.py single <your-file-name>.json -v users=100000 -v buses=200 -v rides_per_user=3
```

The variables flag can override any global variable defined in the JSON file. Multiple variables can be set using multiple `-v` or `--variables` flags.

2. **Run a simulation over multiple periods**:
```bash
python main.py simulate <your-file-name>.json [--periods NUMBER]

# Examples:
python main.py simulate <your-file-name>.json
python main.py simulate <your-file-name>.json --periods 24
python main.py simulate <your-file-name>.json -p 36
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

### Special Variables

You can override any global variable when generating a single report. The available variables are:

3. **System**:
   - `month_from_startup`: Months since startup began

All variables must be numeric values. The tool will attempt to convert input to floating-point numbers.

## Expression Language and Special Features

### Reserved Keywords

The following keywords have special meaning in expressions and cannot be used as variable names:

- `global`: Used to access global variables (e.g., `global.users`)
- `result`: Used in for-loops and exec blocks to store the final value
- `i`: Used as the iteration counter in for-loops (1-based indexing)
- `and`, `or`: Used for boolean operations in case conditions
- `random`: Used as part of the `$random()` function call

### Special Variables

1. **For-loop Variables**:
   - `i`: Current iteration number (1-based indexing)
   - `result`: The value to be aggregated across iterations

2. **Preprocessed Variables**:
   - Available only within their calculation function scope
   - Can reference other preprocessed variables defined earlier
   - Cannot be named using reserved keywords

### Edge Cases and Error Handling

1. **Variable Growth**:
   - **Linear Growth**: When `growth_rate.type` is "linear"
     ```json
     "growth_rate": {
       "type": "linear",
       "values": 0.1  // 10% growth per period
     }
     ```
     - The value is updated as: `base_value * (1 + rate)**period`
     - Zero or negative rates are allowed but may not make business sense
     - A "max" constraint can be specified to cap growth

   - **Logistic Growth**: When `growth_rate.type` is "logistic"
     ```json
     "growth_rate": {
       "type": "logistic",
       "values": {
         "k": 1000000,  // Carrying capacity
         "r": 0.1       // Growth rate
       }
     }
     ```
     - Uses formula: `K / (1 + ((K-N0)/N0) * e**(-r*t))`
     - Handles zero initial values by starting at 0.1% of carrying capacity
     - Useful for modeling S-shaped growth curves

2. **Zero Handling**:
   - Division by zero is caught and raises an error
   - Zero initial values in logistic growth use a small non-zero start value
   - Zero iterations in for-loops return 0 for sum/average, undefined for min/max

3. **Numeric Precision**:
   - All numeric calculations use 64-bit floating point
   - Currency values maintain precision up to 6 decimal places
   - Large numbers (>1e15) may lose precision and should be avoided

4. **Type Conversions**:
   - String numeric values are automatically converted to numbers
   - Boolean expressions evaluate to 1.0 (true) or 0.0 (false)
   - Non-numeric strings in numeric contexts raise errors

### Expression Rules and Syntax

1. **Mathematical Operators**:
   - Standard operators: `+`, `-`, `*`, `/`, `**` (power)
   - Parentheses `()` for grouping
   - Scientific notation (e.g., `1e-8`)

2. **Comparison Operators**:
   - Equal: `==`
   - Not equal: `!=`
   - Greater/Less than: `>`, `<`
   - Greater/Less than or equal: `>=`, `<=`

3. **Logical Operators**:
   - `and`: Both conditions must be true
   - `or`: Either condition must be true
   - Conditions can be nested with parentheses

4. **Special Functions**:
   - `$random(min, max, mean)`: Generates skewed random values
   - Function arguments can be literals or global variables
   - Missing or invalid arguments raise errors

### Formula Evaluation Order

1. **Preprocessing Phase**:
   ```json
   "preprocess": {
     "var1": "global.users * 2",
     "var2": "var1 * global.price"  // Can use var1
   }
   ```
   - Variables are processed in order
   - Later variables can reference earlier ones
   - Circular references raise errors

2. **For-loop Processing**:
   ```json
   "for": {
     "iterator": "iterations",
     "aggregation": "sum",
     "exec": [
       "temp = global.base * i",
       "result = temp * 2"
     ]
   }
   ```
   - Iterator value is calculated first
   - Each iteration creates a fresh variable scope
   - Last `result` assignment is used for aggregation

3. **Case Evaluation**:
   ```json
   "cases": [
     {
       "case": "value < 100",
       "result": "value * 2"
     }
   ]
   ```
   - Cases are evaluated in order
   - First matching case is used
   - No match raises an error

### Best Practices

1. **Variable Naming**:
   - Use descriptive names
   - Avoid reserved keywords
   - Prefix globals with `global.`
   - Use snake_case for consistency

2. **Error Prevention**:
   - Always provide default cases
   - Check for division by zero
   - Validate growth rate parameters
   - Set reasonable min/max bounds

3. **Performance**:
   - Minimize nested calculations
   - Use preprocessing for repeated values
   - Cache common subexpressions
   - Consider numeric precision needs