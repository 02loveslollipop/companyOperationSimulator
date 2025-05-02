import json
from datetime import datetime
from pathlib import Path
import click

from models.entities import (
    CostStructure, 
    Category, 
    GlobalVars, 
    Resource, 
    CalculationFunction,
    CalculationFunctionCase
)
from calculator.calculators import CostCalculator

class JsonParser:
    """Parser class to load and parse the cost calculator JSON structure"""
    @staticmethod
    def parse_calculation_function(data: dict) -> CalculationFunction:
        if isinstance(data, str):
            return CalculationFunction(direct_formula=data)
        
        result = CalculationFunction()
        
        if "preprocess" in data:
            result.preprocess = data["preprocess"]
        
        if "cases" in data:
            result.cases = [
                CalculationFunctionCase(
                    case=case["case"],
                    result=case["result"]
                ) for case in data["cases"]
            ]
        
        if "for" in data:
            result.for_loop = data["for"]
            
        return result

    @staticmethod
    def parse_resource(data: dict) -> Resource:
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
        return Category(
            description=data["description"],
            resource=[JsonParser.parse_resource(r) for r in data["resource"]]
        )

    @staticmethod
    def parse_global_vars(data: dict) -> GlobalVars:
        return GlobalVars(
            const=data["const"],
            variable=data["variable"]
        )

    @staticmethod
    def load(file_path: str) -> CostStructure:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Parse each section into appropriate dataclass objects
        costs = {
            name: JsonParser.parse_category(category) 
            for name, category in data["cost"].items()
        }
        global_vars = JsonParser.parse_global_vars(data["global"])
        income = JsonParser.parse_category(data["income"])
        
        return CostStructure(
            cost=costs,
            global_vars=global_vars,
            income=income
        )

def save_report(report, base_path: str, report_type: str):
    """Save a report to a file"""
    timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{base_path}_{report_type}_{timestamp}"
    
    # Save as JSON
    with open(f"{filename}.json", 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    # Save as CSV
    with open(f"{filename}.csv", 'w') as f:
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

def save_simulation(reports, base_path: str):
    """Save simulation results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_path}_simulation_{timestamp}"
    
    # Save as JSON
    with open(f"{filename}.json", 'w') as f:
        json.dump([r.to_dict() for r in reports], f, indent=2)
    
    # Save as CSV with period columns
    with open(f"{filename}.csv", 'w') as f:
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

def parse_variables(variables):
    """Parse variable overrides from Click's tuple format"""
    if not variables:
        return None
        
    result = {}
    for var in variables:
        name, value = var.split('=')
        try:
            # Try to convert to number
            result[name] = float(value)
        except ValueError:
            # If not a number, keep as string
            result[name] = value
    return result

@click.group()
def cli():
    """Cost Calculator - A tool for calculating and simulating business costs and income"""
    pass

@cli.command()
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--variables', '-v', multiple=True, help='Global variables to override (format: name=value)')
def single(json_file, variables):
    """Generate a single cost report"""
    calculator = CostCalculator(JsonParser.load(json_file))
    global_vars = parse_variables(variables)
    
    report = calculator.generate_report(global_vars)
    base_path = Path(json_file).with_suffix('')
    save_report(report, str(base_path), "single")
    
    click.echo(f"Report generated successfully!")
    click.echo(f"Total Cost: ${report.total_cost:,.2f}")
    click.echo(f"Total Income: ${report.total_income:,.2f}")
    click.echo(f"Net Result: ${report.net_result:,.2f}")

@cli.command()
@click.argument('json_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--periods', '-p', default=12, help='Number of periods to simulate')
def simulate(json_file, periods):
    """Run a cost simulation over multiple periods"""
    calculator = CostCalculator(JsonParser.load(json_file))
    
    with click.progressbar(length=periods, label='Running simulation') as bar:
        reports = calculator.simulate(periods)
        for _ in range(periods):  # Fixed missing parenthesis
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

if __name__ == '__main__':
    cli()