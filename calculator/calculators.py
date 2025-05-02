import logging
from datetime import datetime
import re
import numpy as np
from typing import Dict, List, Union, Optional

from models.entities import CostStructure, CostReport
from utils.SkewedRandomGenerator import SkewedRandomGenerator

class Calculator:
    """Base calculator class that handles formula evaluation"""
    logger = logging.getLogger('Calculator')
    
    def __init__(self):
        self.local_vars: Dict[str, Union[int, float, str]] = {}
        self.global_vars: Dict[str, Union[int, float, str]] = {}
    
    def _preprocess_formula(self, formula: Union[str, int, float]) -> str:
        """Preprocess a formula to handle variables and math operators"""
        self.logger.debug(f"_preprocess_formula input type: {type(formula)}, value: {formula}")
        
        # Ensure formula is a string
        if isinstance(formula, (int, float)):
            self.logger.debug(f"Converting numeric value {formula} to string")
            return str(float(formula))

        # Now we know formula is a string
        formula = str(formula).strip()
        
        # Handle string numeric values
        if formula.isdigit():
            self.logger.debug(f"Found pure integer string: {formula}")
            return formula
        if formula.replace('.','',1).isdigit() and formula.count('.') < 2:
            self.logger.debug(f"Found float string: {formula}")
            return formula
            
        # Replace variable references
        eval_formula = formula
        self.logger.debug(f"Starting variable replacement on: {eval_formula}")
        
        # Handle global variables
        if 'global.' in eval_formula:
            self.logger.debug("Processing global variables")
            for var_name, value in self.global_vars.items():
                old_formula = eval_formula
                eval_formula = eval_formula.replace(f'global.{var_name}', str(float(value)))
                if old_formula != eval_formula:
                    self.logger.debug(f"Replaced global.{var_name}={value} -> {eval_formula}")
                
        # Handle local variables
        self.logger.debug("Processing local variables")
        for var_name, value in self.local_vars.items():
            old_formula = eval_formula
            # Replace only exact variable matches to avoid partial replacements
            eval_formula = re.sub(rf'\b{var_name}\b', str(float(value)), eval_formula)
            if old_formula != eval_formula:
                self.logger.debug(f"Replaced {var_name}={value} -> {eval_formula}")
            
        # Handle math operations
        eval_formula = eval_formula.replace('and', ' and ')
        eval_formula = eval_formula.replace('or', ' or ')
        
        self.logger.debug(f"Final preprocessed formula: {eval_formula}")
        return eval_formula

    def evaluate_formula(self, formula: Union[str, int, float], local_vars: Optional[Dict] = None) -> Union[float, bool]:
        """Evaluate a formula string using the calculator's variables"""
        if local_vars:
            self.logger.debug(f"Evaluating formula with local vars: {local_vars}")
            # Update local variables, converting to float where needed
            self.local_vars.update({k: float(v) if isinstance(v, (int, float)) else v 
                                  for k, v in local_vars.items()})
        
        self.logger.debug(f"Evaluating formula: {formula} (type: {type(formula)})")
        
        try:
            # Handle simple numeric values directly
            if isinstance(formula, (int, float)):
                self.logger.debug(f"Converting numeric value {formula} to float")
                return float(formula)
            
            # Handle string numeric values
            if isinstance(formula, str):
                formula = formula.strip()
                if formula.isdigit():
                    self.logger.debug(f"Converting string integer '{formula}' to float")
                    return float(formula)
                if formula.replace('.','',1).isdigit() and formula.count('.') < 2:
                    self.logger.debug(f"Converting string float '{formula}' to float")
                    return float(formula)
                
            # First preprocess formula to handle variables
            eval_formula = self._preprocess_formula(str(formula))
            self.logger.debug(f"Preprocessed formula: {eval_formula}")
            
            # Check if formula contains comparison operators
            if any(op in eval_formula for op in ['<', '>', '=']):
                result = eval(eval_formula, {"__builtins__": None})
                self.logger.debug(f"Boolean evaluation result: {result}")
                return result
            else:
                result = eval(eval_formula, {"__builtins__": None})
                float_result = float(result)
                self.logger.debug(f"Numeric evaluation result: {float_result}")
                return float_result
                
        except SyntaxError as e:
            error_msg = f"Syntax error in formula at position {e.offset}:\n{self._format_error_location(str(formula), e.offset)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except NameError as e:
            # Find the undefined variable
            var_match = re.search(r"name '(.+)' is not defined", str(e))
            var_name = var_match.group(1) if var_match else "unknown"
            error_msg = f"Undefined variable '{var_name}' in formula:\n{formula}\nAvailable variables: {list(self.local_vars.keys())}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error evaluating formula '{formula}' (type: {type(formula)}): {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Local vars: {self.local_vars}")
            self.logger.error(f"Global vars: {self.global_vars}")
            raise ValueError(error_msg)

    def _format_error_location(self, formula: str, error_position: int) -> str:
        """Format an error location with an underline"""
        if error_position < 0:
            error_position = 0
        return f"{formula}\n{' ' * error_position}^"

    def _process_random(self, params: str) -> float:
        """Process a random function call with parameters"""
        self.logger.debug("Processing $random function call")
        
        # First preprocess the parameters to handle global variables
        processed_params = []
        for param in params.split(','):
            param = param.strip()
            if 'global.' in param:
                # Handle global variable reference
                var_name = param.replace('global.', '')
                if var_name not in self.global_vars:
                    raise ValueError(f"Undefined global variable '{var_name}' in random function parameters")
                processed_params.append(str(self.global_vars[var_name]))
            else:
                processed_params.append(param)
        
        # Now convert parameters to float
        try:
            min_val, max_val, mean = map(float, processed_params)
        except ValueError as e:
            raise ValueError(f"Invalid parameter values for random function: {processed_params}. All parameters must be numeric.")
        
        # Create random generator
        self.logger.debug(f"Creating new random generator for: min={min_val}, max={max_val}, mean={mean}")
        generator = SkewedRandomGenerator(min_val, max_val, mean)
        
        # Generate and return random value
        value = generator.random()
        self.logger.debug(f"Generated random value: {value}")
        return value

    def evaluate_with_functions(self, formula: str, local_vars: Optional[Dict] = None) -> float:
        """Evaluate a formula that may contain function calls"""
        if isinstance(formula, (int, float)):
            return float(formula)
            
        if not isinstance(formula, str):
            raise ValueError(f"Formula must be a string, got {type(formula)}")
            
        # Update local variables
        if local_vars:
            self.local_vars.update(local_vars)
            
        # Handle special functions
        if '$random' in formula:
            # Extract function parameters
            match = re.search(r'\$random\((.*?)\)', formula)
            if not match:
                raise ValueError("Invalid random function call")
                
            params = match.group(1)
            try:
                result = str(self._process_random(params))
                formula = formula.replace(match.group(0), result)
            except Exception as e:
                raise ValueError(f"Error processing random function: {str(e)}")
                
        # Now evaluate the formula
        return self.evaluate_formula(formula)

class ResourceEvaluationError(Exception):
    """Exception raised when evaluating a resource calculation fails"""
    def __init__(self, resource_name: str, category: str, message: str):
        self.resource_name = resource_name
        self.category = category
        self.message = message
        super().__init__(self.format_error())
    
    def format_error(self) -> str:
        """Format the error message with resource context"""
        return f"Error evaluating resource '{self.resource_name}' in category '{self.category}':\n{self.message}"

class CostCalculator:
    """Main calculator class that handles cost structure calculations"""
    logger = logging.getLogger('CostCalculator')
    
    def __init__(self, cost_structure: CostStructure):
        self.cost_structure = cost_structure
        self.calculator = Calculator()
        # Initialize calculator with global variables including variable start values
        self.calculator.global_vars = self.cost_structure.global_vars.get_initial_values()

    def _calculate_resource_cost(self, resource, category_name: str, global_vars: Optional[Dict] = None) -> float:
        """Calculate the cost for a single resource"""
        self.logger.debug(f"Calculating cost for resource: {resource.name}")
        
        try:
            # Set up calculator with global variables
            if global_vars is not None:
                self.calculator.global_vars = global_vars

            # Process preprocessing variables if they exist
            if resource.calculation_function.preprocess:
                self.logger.info("Processing preprocessing variables")
                local_vars = {}
                for var_name, formula in resource.calculation_function.preprocess.items():
                    try:
                        self.logger.debug(f"Evaluating preprocessed variable: {var_name} = {formula}")
                        local_vars[var_name] = self.calculator.evaluate_with_functions(formula)
                    except ValueError as e:
                        raise ValueError(f"Error preprocessing variable '{var_name}': {str(e)}")
            else:
                local_vars = {}

            # Handle different calculation methods
            if resource.calculation_function.cases:
                self.logger.info(f"Evaluating {len(resource.calculation_function.cases)} cases")
                # Try each case
                for case in resource.calculation_function.cases:
                    self.logger.debug(f"Checking case condition: {case.case}")
                    try:
                        if self.calculator.evaluate_formula(case.case, local_vars):
                            self.logger.debug(f"Case matched, evaluating result: {case.result}")
                            # Handle simple integer/float results
                            if case.result.strip().isdigit() or case.result.replace('.','',1).isdigit():
                                return float(case.result)
                            return self.calculator.evaluate_with_functions(case.result, local_vars)
                    except ValueError as e:
                        raise ValueError(f"Error evaluating case condition '{case.case}': {str(e)}")
                        
                raise ValueError(f"No case condition matched for this resource")
                
            elif resource.calculation_function.for_loop:
                self.logger.info("Processing for loop structure")
                loop_struct = resource.calculation_function.for_loop
                
                try:
                    # Get iterator count from preprocessed variable
                    iterator_name = loop_struct.get("iterator")
                    if not iterator_name or iterator_name not in local_vars:
                        raise ValueError(f"Iterator {iterator_name} not found in preprocessed variables")
                    
                    iterations = int(local_vars[iterator_name])
                    self.logger.debug(f"Loop will run for {iterations} iterations")
                    
                    # Initialize result accumulator
                    total = 0
                    
                    # Analyze loop expressions for optimization
                    exec_steps = loop_struct.get("exec", [])
                    static_expressions = []
                    has_dynamic_expressions = False
                    
                    # Pre-analyze expressions to identify static ones
                    for step in exec_steps:
                        # Skip assignment steps for static analysis
                        if "=" in step:
                            has_dynamic_expressions = True
                            continue
                            
                        # Check if expression contains iteration variable 'i'
                        if 'i' not in step and not any(v for v in self.calculator.local_vars if v in step):
                            # Expression is static, can be pre-evaluated
                            static_expressions.append({
                                'expr': step,
                                'value': None  # Will be evaluated on first use
                            })
                        else:
                            has_dynamic_expressions = True
                            
                    # Execute loop steps for each iteration
                    for i in range(iterations):
                        iteration_vars = local_vars.copy()
                        iteration_vars['i'] = i + 1  # 1-based indexing
                        
                        # Handle static expressions first
                        for static_expr in static_expressions:
                            if static_expr['value'] is None:
                                # First time seeing this expression, evaluate and cache
                                static_expr['value'] = self.calculator.evaluate_with_functions(static_expr['expr'], iteration_vars)
                            iteration_vars['result'] = static_expr['value']
                        
                        # Only process dynamic expressions if they exist
                        if has_dynamic_expressions:
                            # Execute each step in the execution list
                            for step in exec_steps:
                                if "=" in step:
                                    # Handle variable assignment
                                    var_name, formula = [x.strip() for x in step.split("=", 1)]
                                    iteration_vars[var_name] = self.calculator.evaluate_with_functions(formula, iteration_vars)
                                else:
                                    # Skip static expressions that were already handled
                                    if not any(se['expr'] == step for se in static_expressions):
                                        # For non-assignment statements, evaluate the expression
                                        result = self.calculator.evaluate_with_functions(step, iteration_vars)
                                        iteration_vars['result'] = result
                        
                        # After all steps, aggregate the final result based on aggregation method
                        if 'result' in iteration_vars:
                            agg_method = loop_struct.get("aggregation", "sum")
                            if agg_method == "sum":
                                total += iteration_vars['result']
                            elif agg_method == "average":
                                total += iteration_vars['result'] / iterations
                            elif agg_method == "max":
                                total = max(total, iteration_vars['result'])
                            elif agg_method == "min":
                                total = min(total, iteration_vars['result']) if i > 0 else iteration_vars['result']
                    
                    self.logger.debug(f"Loop final result after {iterations} iterations: {total}")
                    return total
                    
                except Exception as e:
                    raise ValueError(f"Error in for loop: {str(e)}")
                
            elif resource.calculation_function.direct_formula:
                self.logger.info("Evaluating direct formula")
                return self.calculator.evaluate_with_functions(
                    resource.calculation_function.direct_formula,
                    local_vars
                )
                
            else:
                raise ValueError("Invalid calculation function structure - no calculation method specified")
                
        except ValueError as e:
            raise ResourceEvaluationError(resource.name, category_name, str(e))
        except Exception as e:
            raise ResourceEvaluationError(resource.name, category_name, f"Unexpected error: {str(e)}")

    def generate_report(self, global_vars: Optional[Dict] = None) -> CostReport:
        """Generate a cost report"""
        self.logger.info("Generating cost report")
        
        # Initialize variables
        if global_vars:
            # Override specified global variables
            current_globals = self.cost_structure.global_vars.get_initial_values()
            current_globals.update(global_vars)
        else:
            current_globals = self.cost_structure.global_vars.get_initial_values()
            
        # Update calculator with current globals
        self.calculator.global_vars = current_globals

        # Calculate costs for each category
        costs = {}
        total_cost = 0
        errors = []
        
        for category_name, category in self.cost_structure.cost.items():
            self.logger.debug(f"Processing category: {category_name}")
            category_costs = {}
            
            for resource in category.resource:
                try:
                    cost = self._calculate_resource_cost(resource, category_name, current_globals)
                    category_costs[resource.name] = cost
                    total_cost += cost
                    self.logger.debug(f"Resource {resource.name} cost: {cost}")
                except ResourceEvaluationError as e:
                    self.logger.error(str(e))
                    errors.append(str(e))
                    category_costs[resource.name] = 0
            
            costs[category_name] = category_costs

        # Calculate income
        self.logger.info("Calculating income")
        income = {}
        total_income = 0
        
        for resource in self.cost_structure.income.resource:
            try:
                value = self._calculate_resource_cost(resource, "income", current_globals)
                income[resource.name] = value
                total_income += value
                self.logger.debug(f"Resource {resource.name} income: {value}")
            except ResourceEvaluationError as e:
                self.logger.error(str(e))
                errors.append(str(e))
                income[resource.name] = 0

        # If there were any errors, raise them all together
        if errors:
            raise ValueError("Multiple errors occurred during report generation:\n" + "\n".join(errors))

        # Create and return report
        report = CostReport(
            timestamp=datetime.now(),
            global_vars=current_globals,
            costs=costs,
            income=income,
            total_cost=total_cost,
            total_income=total_income,
            net_result=total_income - total_cost
        )
        
        self.logger.info(f"Report generation completed with total cost: {total_cost}, total income: {total_income}")
        return report

    def simulate(self, periods: int) -> List[CostReport]:
        """Run a simulation over multiple periods"""
        self.logger.info(f"Starting simulation for {periods} periods")
        reports = []
        
        # Generate report for each period
        for i in range(periods):
            self.logger.debug(f"Generating report for period {i+1}/{periods}")
            # Create a copy of global variables
            current_globals = self.cost_structure.global_vars.get_initial_values()
            
            # Update variables that change over time
            for var_name, var_config in self.cost_structure.global_vars.variable.items():
                if "growth" in var_config:
                    growth = float(var_config["growth"])
                    base = float(current_globals[var_name])
                    current_globals[var_name] = base * ((1 + growth) ** i)
                    self.logger.debug(f"Updated variable {var_name} for period {i+1}: {current_globals[var_name]}")
            
            # Generate report with updated variables
            report = self.generate_report(current_globals)
            reports.append(report)
        
        self.logger.info(f"Simulation completed, generated {len(reports)} reports")
        return reports