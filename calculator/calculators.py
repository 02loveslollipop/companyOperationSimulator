from datetime import datetime
from typing import Dict, List, Union
import re

from models.entities import CostStructure, CostReport
from utils.SkewedRandomGenerator import SkewedRandomGenerator

class Calculator:
    """Calculator class that evaluates calculation functions"""
    def __init__(self, global_vars: Dict[str, Union[int, float, str]]):
        self.global_vars = global_vars
        self.random_generators = {}

    def _eval_formula(self, formula: str, local_vars: Dict[str, Union[int, float, str]] = None) -> float:
        """Evaluates a formula string using the global and local context"""
        if not isinstance(formula, str):
            return float(formula)

        context = self.global_vars.copy()
        if local_vars:
            context.update(local_vars)
        
        # Replace global. prefix with nothing since we merged contexts
        formula = formula.replace("global.", "")

        # Replace power operator ^ with ** for Python
        formula = formula.replace("^", "**")
        
        # Handle special $random function
        if "$random" in formula:
            random_calls = re.findall(r'\$random\((.*?)\)', formula)
            for call in random_calls:
                # First evaluate the arguments in case they contain variables
                args = [float(eval(x.strip(), {"__builtins__": {}}, context)) for x in call.split(',')]
                key = f"{args[0]}_{args[1]}_{args[2]}"
                if key not in self.random_generators:
                    self.random_generators[key] = SkewedRandomGenerator(args[0], args[1], args[2])
                random_val = self.random_generators[key].random()
                formula = formula.replace(f"$random({call})", str(random_val))

        # If formula contains comparison operators or boolean operators, evaluate as boolean
        if any(op in formula for op in ['<=', '>=', '<', '>', '==']) or ' and ' in formula or ' or ' in formula:
            try:
                return bool(eval(formula, {"__builtins__": {}}, context))
            except TypeError:
                # If we get a type error, it means we're trying to evaluate a comparison
                # that resulted in a boolean value
                return eval(formula, {"__builtins__": {}}, context)
        
        return float(eval(formula, {"__builtins__": {}}, context))

    def evaluate_function(self, calc_function) -> float:
        """Evaluates a calculation function and returns the result"""
        local_vars = {}
        
        # Handle preprocessing
        if calc_function.preprocess:
            for var_name, formula in calc_function.preprocess.items():
                local_vars[var_name] = self._eval_formula(formula)
        
        # Handle direct formula
        if calc_function.direct_formula:
            return self._eval_formula(calc_function.direct_formula, local_vars)
        
        # Handle cases
        if calc_function.cases:
            for case in calc_function.cases:
                if self._eval_formula(case.case, local_vars):
                    return self._eval_formula(case.result, local_vars)
            raise ValueError("No matching case found")
        
        # Handle for loops
        if calc_function.for_loop:
            iterations = int(self._eval_formula(calc_function.for_loop["iterator"], local_vars))
            results = []
            
            for _ in range(iterations):
                loop_vars = local_vars.copy()
                for statement in calc_function.for_loop["exec"]:
                    if statement.startswith("result ="):
                        results.append(self._eval_formula(statement[8:], loop_vars))
                    else:
                        var_name, formula = statement.split("=")
                        loop_vars[var_name.strip()] = self._eval_formula(formula, loop_vars)
            
            # Apply aggregation
            if not results:  # Handle empty results list
                return 0
            elif calc_function.for_loop["aggregation"] == "sum":
                return sum(results)
            elif calc_function.for_loop["aggregation"] == "average":
                return sum(results) / len(results)
            elif calc_function.for_loop["aggregation"] == "max":
                return max(results)
            elif calc_function.for_loop["aggregation"] == "min":
                return min(results)
            
        raise ValueError("Invalid calculation function structure")

class CostCalculator:
    """Main calculator class that generates cost reports"""
    def __init__(self, structure: CostStructure):
        self.structure = structure

    def generate_report(self, global_vars: Dict[str, Union[int, float, str]] = None) -> CostReport:
        """Generate a cost report for given global variables"""
        if global_vars is None:
            global_vars = {k: v for k, v in self.structure.global_vars.const.items()}
            global_vars.update({k: v["start"] for k, v in self.structure.global_vars.variable.items()})
        
        calculator = Calculator(global_vars)
        
        # Calculate costs
        costs = {}
        total_cost = 0
        for category_name, category in self.structure.cost.items():
            costs[category_name] = {}
            for resource in category.resource:
                try:
                    cost = calculator.evaluate_function(resource.calculation_function)
                    costs[category_name][resource.name] = cost
                    total_cost += cost
                except Exception as e:
                    print(f"Error calculating cost for {resource.name}: {e}")
        
        # Calculate income
        income = {}
        total_income = 0
        for resource in self.structure.income.resource:
            try:
                inc = calculator.evaluate_function(resource.calculation_function)
                income[resource.name] = inc
                total_income += inc
            except Exception as e:
                print(f"Error calculating income for {resource.name}: {e}")
        
        return CostReport(
            timestamp=datetime.now(),
            global_vars=global_vars,
            costs=costs,
            income=income,
            total_cost=total_cost,
            total_income=total_income,
            net_result=total_income - total_cost
        )

    def simulate(self, periods: int) -> List[CostReport]:
        """Run a simulation for the specified number of periods"""
        reports = []
        
        # Initialize variables
        global_vars = {k: v for k, v in self.structure.global_vars.const.items()}
        variable_vars = {k: v["start"] for k, v in self.structure.global_vars.variable.items()}
        global_vars.update(variable_vars)
        
        for period in range(periods):
            # Generate report for current state
            report = self.generate_report(global_vars)
            reports.append(report)
            
            # Update variables according to their growth rates
            for var_name, var_config in self.structure.global_vars.variable.items():
                if "growth_rate" in var_config:
                    current = global_vars[var_name]
                    if var_config["growth_rate"]["type"] == "linear":
                        growth = current * var_config["growth_rate"]["values"]
                    else:
                        raise ValueError(f"Unknown growth rate type: {var_config['growth_rate']['type']}")
                    
                    new_value = current + growth
                    if "max" in var_config:
                        new_value = min(new_value, var_config["max"])
                    global_vars[var_name] = new_value
                
                if "increment" in var_config:
                    global_vars[var_name] += var_config["increment"]
        
        return reports