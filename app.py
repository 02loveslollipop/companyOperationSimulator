import streamlit as st
import pandas as pd
import numpy as np
import json
import io
import plotly.graph_objects as go
from typing import List
import logging
from pkg.models.entities import (
    CostStructure, 
    Category, 
    GlobalVars, 
    Resource, 
    CalculationFunction,
    CalculationFunctionCase,
    CostReport
)
from pkg.calculator.calculators import CostCalculator, ResourceEvaluationError
from cli import JsonParser, JsonParsingError # Import parser and custom error

# --- Logging Setup ---
log_stream = io.StringIO()
logging.basicConfig(stream=log_stream, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def create_detailed_report_df(report: CostReport, cost_structure: CostStructure) -> pd.DataFrame:
    """Creates a DataFrame for the detailed single period report."""
    data = []
    # Costs
    for cat_name, resources in report.costs.items():
        category_obj = cost_structure.cost.get(cat_name)
        if not category_obj: continue
        for res_name, value in resources.items():
            resource_obj = next((r for r in category_obj.resource if r.name == res_name), None)
            if resource_obj:
                data.append({
                    "Type": "Cost",
                    "Category": cat_name,
                    "Resource": res_name,
                    "Value": value,
                    "Use Case": resource_obj.use_case,
                    "Unit": resource_obj.unit,
                    "Calculation Method": resource_obj.calculation_method,
                    "Billing Method": resource_obj.billing_method
                })
    # Income
    income_category = cost_structure.income
    for res_name, value in report.income.items():
         resource_obj = next((r for r in income_category.resource if r.name == res_name), None)
         if resource_obj:
            data.append({
                "Type": "Income",
                "Category": "Income", # Or use income_category.description
                "Resource": res_name,
                "Value": value,
                "Use Case": resource_obj.use_case,
                "Unit": resource_obj.unit,
                "Calculation Method": resource_obj.calculation_method,
                "Billing Method": resource_obj.billing_method
            })

    df = pd.DataFrame(data)
    return df

def plot_simulation(reports: List[CostReport]):
    """Plots income and spending over simulation periods using Plotly."""
    periods = list(range(1, len(reports) + 1))
    total_costs = [r.total_cost for r in reports]
    total_incomes = [r.total_income for r in reports]
    net_results = [r.net_result for r in reports]

    fig = go.Figure()

    # Add traces
    fig.add_trace(go.Scatter(x=periods, y=total_costs, mode='lines+markers', name='Total Cost', marker=dict(symbol='circle')))
    fig.add_trace(go.Scatter(x=periods, y=total_incomes, mode='lines+markers', name='Total Income', marker=dict(symbol='circle')))
    fig.add_trace(go.Scatter(x=periods, y=net_results, mode='lines+markers', name='Net Result', marker=dict(symbol='square'), line=dict(dash='dash')))

    # Update layout
    fig.update_layout(
        title='Simulation Results Over Time',
        xaxis_title='Period (Month)',
        yaxis_title='Amount ($)',
        legend_title='Metric',
        hovermode="x unified" # Improves hover experience
    )
    fig.update_xaxes(dtick=1) # Ensure integer ticks for periods
    fig.update_yaxes(tickprefix="$", tickformat=",.2f")

    # Display using Streamlit's Plotly chart function
    st.plotly_chart(fig, use_container_width=True)

# Initialize session state if needed
if "simulation_run" not in st.session_state:
    st.session_state.simulation_run = False
if "reports" not in st.session_state:
    st.session_state.reports = None
if "cost_structure" not in st.session_state:
    st.session_state.cost_structure = None
if "forecast_periods" not in st.session_state:
    st.session_state.forecast_periods = 1
if "global_overrides" not in st.session_state:
    st.session_state.global_overrides = {}

# --- Streamlit App ---

st.set_page_config(page_title="Company Operation Simulator", layout="wide", initial_sidebar_state="expanded", page_icon="📊")
st.title("📊 Company Operation Simulator Dashboard")

# Function to detect if key simulation inputs have changed
def has_simulation_inputs_changed(cost_structure, forecast_periods, global_overrides):
    if not st.session_state.simulation_run:
        return True
    if st.session_state.forecast_periods != forecast_periods:
        return True
    if st.session_state.cost_structure != cost_structure:
        return True
    # Compare global overrides
    if st.session_state.global_overrides != global_overrides:
        return True
    return False

# --- File Upload ---
uploaded_file = st.file_uploader("Choose your input.json file", type="json")

if uploaded_file is not None:
    # To read file as string:
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    file_content = stringio.read() # Keep content for potential error reporting
    
    try:
        # Use a temporary file path for error reporting if needed
        temp_file_path = uploaded_file.name 
        # Parse the JSON content using the existing parser
        # We need to load it into a dict first for the parser structure
        json_data = json.loads(file_content) 
        
        # Manually parse using the static methods from JsonParser
        costs = {
            name: JsonParser.parse_category(category) 
            for name, category in json_data["cost"].items()
        }
        global_vars_data = JsonParser.parse_global_vars(json_data["global"])
        income = JsonParser.parse_category(json_data["income"])
        
        cost_structure = CostStructure(
            cost=costs,
            global_vars=global_vars_data,
            income=income
        )
        
        st.success("✅ JSON file loaded and parsed successfully!")

        # --- Main Dashboard Area ---
        forecast_periods = st.number_input("**Forecast Periods (Months)**", min_value=1, value=1, step=1)

        # --- Sidebar Inputs ---
        st.sidebar.header("Simulation Parameters")
        
        # Store overrides
        global_overrides = {}

        st.sidebar.subheader("Global Constants")
        for name, value in cost_structure.global_vars.const.items():
             # Use text input for strings, number for numeric
             if isinstance(value, str):
                 global_overrides[name] = st.sidebar.text_input(f"Const: {name}", value=value)
             else:
                 global_overrides[name] = st.sidebar.number_input(f"Const: {name}", value=float(value), format="%.2f")

        st.sidebar.subheader("Global Variables (Initial Values)")
        initial_variable_values = cost_structure.global_vars.get_initial_values()
        for name, config in cost_structure.global_vars.variable.items():
            # Get initial value, might be overridden later
            start_value = initial_variable_values.get(name, 0.0) 
            global_overrides[name] = st.sidebar.number_input(
                f"Var: {name}", 
                value=float(start_value), 
                help=f"Config: {config}", 
                format="%.2f"
            )

        # --- Calculation and Display Logic ---
        try:
            # Clear the log stream before each calculation
            log_stream.seek(0)
            log_stream.truncate(0)
            
            # Check if we need to run a new simulation or can use cached results
            inputs_changed = has_simulation_inputs_changed(cost_structure, forecast_periods, global_overrides)
            
            calculator = CostCalculator(cost_structure)
            
            if forecast_periods == 1:
                st.header("Single Period Report")
                
                # Always regenerate for single period (it's fast)
                report = calculator.generate_report(global_overrides)
                
                st.subheader("Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Income", f"${report.total_income:,.2f}")
                col2.metric("Total Cost", f"${report.total_cost:,.2f}")
                col3.metric("Net Result", f"${report.net_result:,.2f}")

                st.subheader("Detailed Breakdown")
                report_df = create_detailed_report_df(report, cost_structure)
                
                # Display DataFrame with tooltips (using st.dataframe)
                st.dataframe(
                    report_df,
                    column_config={
                        "Value": st.column_config.NumberColumn(format="$%.2f"),
                        "Calculation Method": st.column_config.TextColumn(help="How the value is calculated."),
                        "Billing Method": st.column_config.TextColumn(help="How the service is billed.")
                    },
                    use_container_width=True,
                    hide_index=True
                )

            else: # Multi-period simulation
                st.header(f"Simulation Report ({forecast_periods} Periods)")
                
                if inputs_changed:
                    with st.spinner(f"Running simulation for {forecast_periods} periods..."):
                        # Re-init calculator to ensure fresh state if needed
                        calculator_sim = CostCalculator(cost_structure) 
                        reports = calculator_sim.simulate(periods=forecast_periods)
                        
                        # Store in session state
                        st.session_state.reports = reports
                        st.session_state.cost_structure = cost_structure
                        st.session_state.forecast_periods = forecast_periods
                        st.session_state.global_overrides = global_overrides.copy()
                        st.session_state.simulation_run = True
                        
                        st.success("✅ Simulation completed!")
                else:
                    # Use cached results
                    st.info("Using cached simulation results. Change inputs to re-run simulation.")
                    reports = st.session_state.reports
                
                st.subheader("Overall Simulation Summary")
                initial_report = reports[0]
                final_report = reports[-1]
                
                total_sim_income = sum(r.total_income for r in reports)
                total_sim_cost = sum(r.total_cost for r in reports)
                total_sim_net = total_sim_income - total_sim_cost

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Income (Sim)", f"${total_sim_income:,.2f}")
                col2.metric("Total Cost (Sim)", f"${total_sim_cost:,.2f}")
                col3.metric("Gross Margin (Sim)", f"${total_sim_net:,.2f}")

                st.subheader("Performance Over Time")
                plot_simulation(reports)

                st.subheader("Detailed Reports")
                # Rearranged tab order to make "Select Period" the first tab
                tab3, tab1, tab2 = st.tabs(["Select Period", "Final Period Accumulated", "Initial Period"])

                # --- Select Period Tab (now first) ---
                with tab3:
                    st.markdown("#### Select Period to View Details")
                    period_options = [f"Period {i+1}" for i in range(len(reports))]
                    
                    # Store the period selection in session state to persist across reruns
                    if "selected_period" not in st.session_state:
                        st.session_state.selected_period = period_options[0]
                        
                    selected_period_str = st.selectbox(
                        "Choose a period:", 
                        period_options,
                        key="selected_period"
                    )
                    
                    selected_index = int(selected_period_str.split(" ")[1]) - 1
                    selected_report = reports[selected_index]

                    st.markdown(f"##### Details for {selected_period_str}")
                    col1_sel, col2_sel, col3_sel = st.columns(3)
                    col1_sel.metric("Total Income", f"${selected_report.total_income:,.2f}")
                    col2_sel.metric("Total Cost", f"${selected_report.total_cost:,.2f}")
                    col3_sel.metric("Net Result", f"${selected_report.net_result:,.2f}")

                    selected_df = create_detailed_report_df(selected_report, cost_structure)
                    st.dataframe(
                        selected_df,
                        column_config={
                            "Value": st.column_config.NumberColumn(format="$%.2f"),
                            "Calculation Method": st.column_config.TextColumn(help="How the value is calculated."),
                            "Billing Method": st.column_config.TextColumn(help="How the service is billed.")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                # --- Final Period Tab (now second) ---
                with tab1:
                    st.markdown("#### Final Period Status")
                    st.metric("Final Net Result", f"${final_report.net_result:,.2f}")
                    final_df = create_detailed_report_df(final_report, cost_structure)
                    st.dataframe(
                        final_df,
                         column_config={
                            "Value": st.column_config.NumberColumn(format="$%.2f"),
                            "Calculation Method": st.column_config.TextColumn(help="How the value is calculated."),
                            "Billing Method": st.column_config.TextColumn(help="How the service is billed.")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                # --- Initial Period Tab (now third) ---
                with tab2:
                    st.markdown("#### Initial Period Status")
                    st.metric("Initial Net Result", f"${initial_report.net_result:,.2f}")
                    initial_df = create_detailed_report_df(initial_report, cost_structure)
                    st.dataframe(
                        initial_df,
                         column_config={
                            "Value": st.column_config.NumberColumn(format="$%.2f"),
                            "Calculation Method": st.column_config.TextColumn(help="How the value is calculated."),
                            "Billing Method": st.column_config.TextColumn(help="How the service is billed.")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

            # --- Display Logs ---
            st.divider() # Add a visual separator
            with st.expander("📄 View Calculation Logs"):
                log_contents = log_stream.getvalue()
                st.text_area("Logs", log_contents, height=300)

        except (ValueError, ResourceEvaluationError, KeyError, Exception) as e:
            st.error(f"❌ Error during calculation: {e}")
            st.exception(e) # Show full traceback for debugging
            # Also display any logs captured before the error
            st.divider()
            with st.expander("📄 View Calculation Logs (Error Occurred)"):
                log_contents = log_stream.getvalue()
                st.text_area("Logs", log_contents, height=300)

    except JsonParsingError as e:
        st.error(f"❌ Error parsing JSON file '{uploaded_file.name}':")
        st.error(e) # Display formatted error from the custom exception
        st.code(e.snippet, language='json') # Show the problematic line
    except Exception as e:
        st.error(f"❌ An unexpected error occurred while loading the file: {e}")
        st.exception(e)

else:
    st.info("☝️ Upload an `input.json` file to begin. Check out the documentation in [wiki](%s) for more details." % "https://github.com/02loveslollipop/companyOperationSimulator/wiki")


