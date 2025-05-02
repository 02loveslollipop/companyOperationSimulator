import json
import logging
from datetime import datetime
from pathlib import Path
import click
import sys

from pkg.models.entities import (
    CostStructure, 
    Category, 
    GlobalVars, 
    Resource, 
    CalculationFunction,
    CalculationFunctionCase
)
from pkg.calculator.calculators import CostCalculator

def setup_logging(verbose: bool):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

class JsonParsingError(Exception):
    """Exception raised for errors during JSON parsing"""
    def __init__(self, message: str, file_path: str, line: int, col: int, snippet: str = None):
        self.message = message
        self.file_path = file_path
        self.line = line
        self.col = col
        self.snippet = snippet
        super().__init__(self.format_error())
    
    def format_error(self) -> str:
        """Format the error message with location information"""
        error = f"JSON parsing error in {self.file_path} at line {self.line}, column {self.col}: {self.message}"
        if self.snippet:
            error += f"\n\n{self.snippet}\n{' ' * self.col}^"
        return error

class JsonParser:
    """Parser class to load and parse the cost calculator JSON structure"""
    logger = logging.getLogger('JsonParser')

    @staticmethod
    def get_line_from_position(content: str, position: int) -> tuple[int, int, str]:
        """Get line number, column and line content from character position"""
        lines = content.split('\n')
        pos = 0
        for i, line in enumerate(lines):
            if pos + len(line) + 1 > position:
                return i + 1, position - pos, line
            pos += len(line) + 1
        return len(lines), 0, ""

    @staticmethod
    def parse_calculation_function(data: dict) -> CalculationFunction:
        JsonParser.logger.debug(f"Parsing calculation function: {json.dumps(data, indent=2)}")
        if isinstance(data, str):
            JsonParser.logger.debug(f"Direct formula found: {data}")
            return CalculationFunction(direct_formula=data)
        
        result = CalculationFunction()
        
        if "preprocess" in data:
            JsonParser.logger.debug(f"Preprocessing variables: {data['preprocess']}")
            result.preprocess = data["preprocess"]
        
        if "cases" in data:
            JsonParser.logger.debug(f"Case conditions found: {len(data['cases'])} cases")
            result.cases = [
                CalculationFunctionCase(
                    case=case["case"],
                    result=case["result"]
                ) for case in data["cases"]
            ]
        
        if "for" in data:
            JsonParser.logger.debug(f"For loop structure found: {data['for']}")
            result.for_loop = data["for"]
            
        return result

    @staticmethod
    def parse_resource(data: dict) -> Resource:
        JsonParser.logger.debug(f"Parsing resource: {data['name']}")
        calculation_function = JsonParser.parse_calculation_function(data["calculation_function"])
        return Resource(
            name=data["name"],
            use_case=data["use_case"],
            calculation_method=data["calculation_method"],
            billing_method=data["billing_method"],
            unit=data["unit"],
            calculation_function=calculation_function
        )

    @staticmethod
    def parse_category(data: dict) -> Category:
        JsonParser.logger.debug(f"Parsing category: {data['description']}")
        return Category(
            description=data["description"],
            resource=[JsonParser.parse_resource(r) for r in data["resource"]]
        )

    @staticmethod
    def parse_global_vars(data: dict) -> GlobalVars:
        JsonParser.logger.debug("Parsing global variables")
        JsonParser.logger.debug(f"Constants: {json.dumps(data['const'], indent=2)}")
        JsonParser.logger.debug(f"Variables: {json.dumps(data['variable'], indent=2)}")
        return GlobalVars(
            const=data["const"],
            variable=data["variable"]
        )

    @staticmethod
    def load(file_path: str) -> CostStructure:
        """Load and parse JSON file with enhanced error handling"""
        JsonParser.logger.info(f"Loading JSON file: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    # Get line number and column from the error position
                    line_num, col, line_content = JsonParser.get_line_from_position(content, e.pos)
                    raise JsonParsingError(
                        message=str(e),
                        file_path=file_path,
                        line=line_num,
                        col=col,
                        snippet=line_content
                    ) from e
        
            JsonParser.logger.debug("Starting JSON structure parsing")
            # Parse each section into appropriate dataclass objects
            try:
                costs = {
                    name: JsonParser.parse_category(category) 
                    for name, category in data["cost"].items()
                }
                global_vars = JsonParser.parse_global_vars(data["global"])
                income = JsonParser.parse_category(data["income"])
            except KeyError as e:
                raise JsonParsingError(
                    message=f"Missing required field: {str(e)}",
                    file_path=file_path,
                    line=0,
                    col=0
                ) from e
            except Exception as e:
                raise JsonParsingError(
                    message=f"Error parsing JSON structure: {str(e)}",
                    file_path=file_path,
                    line=0,
                    col=0
                ) from e
            
            JsonParser.logger.info("JSON structure parsing completed")
            return CostStructure(
                cost=costs,
                global_vars=global_vars,
                income=income
            )
        except FileNotFoundError:
            raise JsonParsingError(
                message=f"File not found: {file_path}",
                file_path=file_path,
                line=0,
                col=0
            )
        except IsADirectoryError:
            raise JsonParsingError(
                message=f"Path is a directory, not a file: {file_path}",
                file_path=file_path,
                line=0,
                col=0
            )

def save_report(report, base_path: str, report_type: str):
    """Save a report to a file"""
    logger = logging.getLogger('save_report')
    timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{base_path}_{report_type}_{timestamp}"
    
    # Save as JSON
    json_file = f"{filename}.json"
    logger.info(f"Saving JSON report to {json_file}")
    with open(json_file, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    # Save as CSV
    csv_file = f"{filename}.csv"
    logger.info(f"Saving CSV report to {csv_file}")
    with open(csv_file, 'w') as f:
        # Write header
        f.write("Category,Resource,Value\n")
        
        # Write costs
        for category, resources in report.costs.items():
            for resource, value in resources.items():
                f.write(f"{category},{resource},{value}\n")
        
        # Write income
        for resource, value in report.income.items():
            f.write(f"income,{resource},{value}\n")
        
        # Write totals
        f.write(f"total,cost,{report.total_cost}\n")
        f.write(f"total,income,{report.total_income}\n")
        f.write(f"total,net_result,{report.net_result}\n")
    
    logger.info("Report files saved successfully")

def save_simulation(reports, base_path: str):
    """Save simulation results to files"""
    logger = logging.getLogger('save_simulation')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_path}_simulation_{timestamp}"
    
    # Save as JSON
    json_file = f"{filename}.json"
    logger.info(f"Saving JSON simulation results to {json_file}")
    with open(json_file, 'w') as f:
        json.dump([r.to_dict() for r in reports], f, indent=2)
    
    # Save as CSV with period columns
    csv_file = f"{filename}.csv"
    logger.info(f"Saving CSV simulation results to {csv_file}")
    with open(csv_file, 'w') as f:
        # Write header
        f.write("Category,Resource," + ",".join(f"Period_{i}" for i in range(len(reports))) + "\n")
        
        # Get all unique category/resource combinations
        rows = []
        for category, resources in reports[0].costs.items():
            for resource in resources:
                rows.append((category, resource))
        for resource in reports[0].income:
            rows.append(("income", resource))
        rows.extend([
            ("total", "cost"),
            ("total", "income"),
            ("total", "net_result")
        ])
        
        # Write data rows
        for category, resource in rows:
            row = f"{category},{resource}"
            for period, report in enumerate(reports):
                if category == "total":
                    if resource == "cost":
                        value = report.total_cost
                    elif resource == "income":
                        value = report.total_income
                    else:
                        value = report.net_result
                elif category == "income":
                    value = report.income[resource]
                else:
                    value = report.costs[category][resource]
                row += f",{value}"
            f.write(row + "\n")
    
    logger.info("Simulation files saved successfully")

def parse_variables(variables):
    """Parse variable overrides from Click's tuple format"""
    logger = logging.getLogger('parse_variables')
    if not variables:
        logger.debug("No variable overrides provided")
        return None
        
    result = {}
    for var in variables:
        name, value = var.split('=')
        try:
            # Try to convert to number
            result[name] = float(value)
            logger.debug(f"Variable override: {name}={value} (numeric)")
        except ValueError:
            # If not a number, keep as string
            result[name] = value
            logger.debug(f"Variable override: {name}={value} (string)")
    return result

@click.group()
def cli():
    """Cost Calculator - A tool for calculating and simulating business costs and income"""
    pass

@cli.command()
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--variables', '-v', multiple=True, help='Global variables to override (format: name=value)')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def single(json_file, variables, verbose):
    """Generate a single cost report"""
    setup_logging(verbose)
    logger = logging.getLogger('single')
    
    try:
        logger.info("Starting single report generation")
        calculator = CostCalculator(JsonParser.load(json_file))
        global_vars = parse_variables(variables)
        
        logger.info("Generating cost report")
        report = calculator.generate_report(global_vars)
        base_path = Path(json_file).with_suffix('')
        save_report(report, str(base_path), "single")
        
        click.echo(f"Report generated successfully!")
        click.echo(f"Total Cost: ${report.total_cost:,.2f}")
        click.echo(f"Total Income: ${report.total_income:,.2f}")
        click.echo(f"Net Result: ${report.net_result:,.2f}")
        logger.info("Single report generation completed")
    except ValueError as e:
        logger.error(f"Error generating report: {e}")
        # Format the error message nicely for the user
        click.echo(click.style("Error: ", fg='red') + str(e), err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        click.echo(click.style("An unexpected error occurred: ", fg='red') + str(e), err=True)
        sys.exit(1)

@cli.command()
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--periods', '-p', default=12, help='Number of periods to simulate')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def simulate(json_file, periods, verbose):
    """Run a cost simulation over multiple periods"""
    setup_logging(verbose)
    logger = logging.getLogger('simulate')
    
    try:
        logger.info(f"Starting simulation for {periods} periods")
        calculator = CostCalculator(JsonParser.load(json_file))
        
        with click.progressbar(length=periods, label='Running simulation') as bar:
            reports = calculator.simulate(periods)
            logger.info(f"Generated {len(reports)} simulation reports")
            for _ in range(periods):
                bar.update(1)
        
        base_path = Path(json_file).with_suffix('')
        save_simulation(reports, str(base_path))
        
        click.echo(f"\nSimulation completed successfully!")
        click.echo(f"Initial period:")
        click.echo(f"  Total Cost: ${reports[0].total_cost:,.2f}")
        click.echo(f"  Total Income: ${reports[0].total_income:,.2f}")
        click.echo(f"  Net Result: ${reports[0].net_result:,.2f}")
        click.echo(f"\nFinal period:")
        click.echo(f"  Total Cost: ${reports[-1].total_cost:,.2f}")
        click.echo(f"  Total Income: ${reports[-1].total_income:,.2f}")
        click.echo(f"  Net Result: ${reports[-1].net_result:,.2f}")
        logger.info("Simulation completed")
    except ValueError as e:
        logger.error(f"Error during simulation: {e}")
        click.echo(click.style("Error: ", fg='red') + str(e), err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        click.echo(click.style("An unexpected error occurred: ", fg='red') + str(e), err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()