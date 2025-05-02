from dataclasses import dataclass
from typing import Dict, List, Union, Optional
import datetime

@dataclass
class CalculationFunctionCase:
    case: str
    result: str

@dataclass 
class CalculationFunction:
    preprocess: Optional[Dict[str, str]] = None
    cases: Optional[List[CalculationFunctionCase]] = None
    for_loop: Optional[Dict] = None
    direct_formula: Optional[str] = None

@dataclass
class Resource:
    name: str
    use_case: str
    calculation_method: str
    billing_method: str
    unit: str
    calculation_function: CalculationFunction

@dataclass
class Category:
    description: str
    resource: List[Resource]

@dataclass
class GlobalVars:
    const: Dict[str, Union[int, float, str]]
    variable: Dict[str, Dict]

    def get_initial_values(self) -> Dict[str, Union[int, float]]:
        """Get initial values for all variables"""
        values = self.const.copy()
        # Add initial values for variable parameters
        for name, config in self.variable.items():
            if "start" in config:
                values[name] = float(config["start"])
        return values

class GlobalVariables:
    """Class representing global variables structure"""
    def __init__(self):
        self.const = {}
        self.variable = {}

    def from_dict(self, data: Dict) -> None:
        """Initialize from dictionary data"""
        if "Constants" in data:
            self.const = data["Constants"]
        if "Variables" in data:
            self.variable = data["Variables"]

@dataclass
class CostStructure:
    cost: Dict[str, Category]
    global_vars: GlobalVars
    income: Category

@dataclass
class CostReport:
    timestamp: datetime
    global_vars: Dict[str, Union[int, float, str]]
    costs: Dict[str, Dict[str, float]]
    income: Dict[str, float]
    total_cost: float
    total_income: float
    net_result: float

    def to_dict(self) -> Dict:
        """Convert the report to a dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "global_vars": self.global_vars,
            "costs": self.costs,
            "income": self.income,
            "total_cost": self.total_cost,
            "total_income": self.total_income,
            "net_result": self.net_result
        }