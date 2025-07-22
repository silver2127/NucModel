import json
from pathlib import Path

import numpy as np
import numpy_financial as npf
import pandas as pd

def calculate_npv(net_cash_flows, discount_rate):
    """
    Calculates the Net Present Value (NPV) for a project.

    This function is based on Formula (1) from the paper "Modern financial 
    models of nuclear power plants" by P. Terlikowski et al.

    Args:
        net_cash_flows (list or np.array): A list of net cash flows (NCF_t) for 
                                          each period t. Cash outflows should be negative.
        discount_rate (float): The discount rate (p) for the calculation, 
                               expressed as a decimal (e.g., 0.05 for 5%).

    Returns:
        float: The calculated Net Present Value of the project.
    """
    npv = 0
    for t, ncf in enumerate(net_cash_flows):
        # The formula uses t=1 to n, so we use t+1 in the denominator
        npv += ncf / ((1 + discount_rate) ** (t + 1))
    return npv

def calculate_lcoe(investment_costs, operation_costs, energy_production, discount_rate, residual_value=0):
    """
    Calculates the Levelized Cost of Energy (LCOE).

    This function is based on the expanded Formula (2) from the paper 
    "Modern financial models of nuclear power plants" by P. Terlikowski et al.

    Args:
        investment_costs (list or np.array): Investment expenditures (I_t) for each year t.
        operation_costs (list or np.array): Operational costs (K_t) for each year t.
        energy_production (list or np.array): Energy produced (A_t) in MWh for each year t.
        discount_rate (float): The discount rate (p) for the calculation, as a decimal.
        residual_value (float, optional): The value of non-amortized assets (WM_n) 
                                          at the end of the analysis period. Defaults to 0.

    Returns:
        float: The calculated Levelized Cost of Energy, typically in currency per MWh.
    """
    # Ensure all lists are the same length for the analysis period n
    if not (len(investment_costs) == len(operation_costs) == len(energy_production)):
        raise ValueError("Input lists for costs and production must have the same length.")
    
    analysis_period_n = len(investment_costs)
    
    # Calculate the numerator: Sum of discounted costs
    discounted_investments = sum(investment_costs[t] / ((1 + discount_rate) ** (t + 1)) for t in range(analysis_period_n))
    discounted_operations = sum(operation_costs[t] / ((1 + discount_rate) ** (t + 1)) for t in range(analysis_period_n))
    discounted_residual_value = residual_value / ((1 + discount_rate) ** analysis_period_n)
    
    total_discounted_costs = discounted_investments + discounted_operations - discounted_residual_value

    # Calculate the denominator: Sum of discounted energy production
    total_discounted_energy = sum(energy_production[t] / ((1 + discount_rate) ** (t + 1)) for t in range(analysis_period_n))

    # Avoid division by zero if no energy is produced
    if total_discounted_energy == 0:
        return float('inf')

    # Calculate LCOE
    lcoe = total_discounted_costs / total_discounted_energy
    return lcoe

def calculate_irr(net_cash_flows):
    """Return the Internal Rate of Return (IRR) for given cash flows."""
    return npf.irr(net_cash_flows)

def calculate_discounted_payback_period(net_cash_flows, discount_rate):
    """Return the discounted payback period in years or None if never recovered."""
    cumulative = 0.0
    for t, ncf in enumerate(net_cash_flows):
        cumulative += ncf / ((1 + discount_rate) ** t)
        if cumulative >= 0:
            return t
    return None


def simulate_plant_operation(prices: pd.DataFrame,
                             capacity_mw: float,
                             fuel_cost_per_mwh: float,
                             maintenance_days: int = 30,
                             capacity_factor: float = 0.9):
    """Simulate operating a plant and selling energy.

    Parameters
    ----------
    prices : pandas.DataFrame
        Hourly price data with ``timestamp`` and ``price`` columns.
    capacity_mw : float
        Nameplate capacity of the plant in MW.
    fuel_cost_per_mwh : float
        Fuel cost per MWh of electricity produced.
    maintenance_days : int, optional
        Number of maintenance days each year where the plant is offline.
    capacity_factor : float, optional
        Operational capacity factor outside of maintenance periods.

    Returns
    -------
    tuple
        Total profit and a DataFrame of the simulation results.
    """

    if prices.empty:
        raise ValueError("Price data required for simulation")

    df = prices.copy().sort_values("timestamp").reset_index(drop=True)
    df["energy_mwh"] = capacity_mw * capacity_factor

    if maintenance_days > 0:
        downtime_hours = int(maintenance_days * 24)
        for year in df["timestamp"].dt.year.unique():
            idx = df.index[df["timestamp"].dt.year == year]
            downtime = idx[:downtime_hours]
            df.loc[downtime, "energy_mwh"] = 0.0

    df["revenue"] = df["price"] * df["energy_mwh"]
    df["fuel_cost"] = fuel_cost_per_mwh * df["energy_mwh"]
    df["profit"] = df["revenue"] - df["fuel_cost"]

    total_profit = df["profit"].sum()
    return total_profit, df


def load_parameters(path: str) -> dict:
    """Load plant parameters from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_example(params: dict) -> None:
    """Execute the financial model using provided parameters and print results."""

    construction_years = params["construction_period_years"]
    operational_years = params["operational_life_years"]
    total_years = construction_years + operational_years
    discount_rate = params["discount_rate"]

    overnight_cost = params["overnight_cost_usd_million"]
    annual_investment = overnight_cost / construction_years

    annual_op_cost = params["annual_operation_cost_usd_million"]
    op_cost_inflation = params["op_cost_inflation"]
    decommissioning = params["decommissioning_cost_usd_million"]
    residual_value = params["residual_value_usd_million"]

    capacity_mw = params["plant_capacity_mw"]
    capacity_factor = params["capacity_factor"]
    electricity_price = params["electricity_price_usd_per_mwh"]

    annual_energy = capacity_mw * 24 * 365 * capacity_factor

    investment_schedule = [annual_investment] * construction_years + [0] * operational_years

    op_cost_schedule = [0] * construction_years
    current_cost = annual_op_cost
    for _ in range(operational_years):
        op_cost_schedule.append(current_cost)
        current_cost *= 1 + op_cost_inflation
    op_cost_schedule[-1] += decommissioning

    energy_schedule = [0] * construction_years
    current_energy = annual_energy
    for _ in range(operational_years):
        energy_schedule.append(current_energy)
        current_energy *= 0.999

    revenue_schedule = [0] * construction_years
    for energy in energy_schedule[construction_years:]:
        revenue_schedule.append((energy * electricity_price) / 1_000_000)

    net_cash_flows = np.array(revenue_schedule) - (
        np.array(investment_schedule) + np.array(op_cost_schedule)
    )

    lcoe_result = calculate_lcoe(
        investment_costs=investment_schedule,
        operation_costs=op_cost_schedule,
        energy_production=energy_schedule,
        discount_rate=discount_rate,
        residual_value=residual_value,
    )

    print("\nProject Parameters:")
    print(f"  - Discount Rate: {discount_rate:.1%}")
    print(
        f"  - Total Lifecycle: {total_years} years ({construction_years} construction + {operational_years} operation)"
    )
    print(f"  - Total Investment: ${overnight_cost:,.0f} Million")
    print(f"  - Annual Energy Output: {annual_energy:,.0f} MWh")

    print("\n--- Model Results ---")
    lcoe_dollars = lcoe_result * 1_000_000
    print(f"Levelized Cost of Energy (LCOE): ${lcoe_dollars:,.2f} per MWh")
    print("\nThis LCOE represents the minimum average price at which electricity must be sold")
    print("for the project to break even over its lifetime (i.e., achieve an NPV of zero).")

    npv_result = calculate_npv(net_cash_flows, discount_rate)
    print(
        f"\nNet Present Value (NPV) at a fixed price of ${electricity_price}/MWh: ${npv_result:,.2f} Million"
    )
    if npv_result > 0:
        print("The project is financially viable under these assumptions, as the NPV is positive.")
    else:
        print("The project is not financially viable under these assumptions, as the NPV is negative.")

    irr_result = calculate_irr(net_cash_flows)
    if irr_result is not None:
        print(f"Internal Rate of Return (IRR): {irr_result:.2%}")
    else:
        print("IRR could not be calculated.")

    payback = calculate_discounted_payback_period(net_cash_flows, discount_rate)
    if payback is not None:
        print(f"Discounted Payback Period: {payback} years")
    else:
        print("Discounted payback period was not reached within the project life.")

    print("\n--- Operational Simulation ---")
    hours = 365 * 24
    timestamps = pd.date_range("2024-01-01", periods=hours, freq="H")
    price_df = pd.DataFrame({"timestamp": timestamps, "price": electricity_price})

    fuel_cost = params.get("fuel_cost_per_mwh", 0)
    maintenance_days = params.get("maintenance_days", 30)
    profit, _ = simulate_plant_operation(
        price_df,
        capacity_mw=capacity_mw,
        fuel_cost_per_mwh=fuel_cost,
        maintenance_days=maintenance_days,
        capacity_factor=capacity_factor,
    )
    print(f"Simulated annual profit: ${profit:,.2f}")

# --- Main execution block with an example scenario ---
def main() -> None:
    params_path = Path(__file__).resolve().parent / "example_plant.json"
    params = load_parameters(params_path)
    print("--- Financial Model for a Hypothetical Nuclear Power Plant ---")
    run_example(params)


if __name__ == "__main__":
    main()
