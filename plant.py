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


def simulate_plant_operation(
    prices: pd.DataFrame,
    capacity_mw: float,
    fuel_cost_per_mwh: float | None = None,
    maintenance_days: int = 30,
    capacity_factor: float = 0.9,
    maintenance_interval_months: int = 12,
    *,
    fuel_cost_per_refueling: float | None = None,
    refueling_cycle_months: int = 18,
):
    """Simulate operating a plant and selling energy.

    Parameters
    ----------
    prices : pandas.DataFrame
        Hourly price data with ``timestamp`` and ``price`` columns.
    capacity_mw : float
        Nameplate capacity of the plant in MW.
    fuel_cost_per_mwh : float, optional
        Fuel cost per MWh of electricity produced. If ``None`` and
        ``fuel_cost_per_refueling`` is provided, this value is
        calculated automatically.
    maintenance_days : int, optional
        Number of maintenance days for each maintenance outage.
    maintenance_interval_months : int, optional
        How often maintenance outages occur, in months. Defaults to 12
        (once per year).
    fuel_cost_per_refueling : float, optional
        Total cost of one refueling cycle. If provided, it will be
        converted to a per-MWh cost based on ``refueling_cycle_months``.
    refueling_cycle_months : int, optional
        Length of a fuel cycle in months. Defaults to 18 months.
    capacity_factor : float, optional
        Operational capacity factor outside of maintenance periods.

    Returns
    -------
    tuple
        Total profit and a DataFrame of the simulation results.
    """

    if prices.empty:
        raise ValueError("Price data required for simulation")

    if fuel_cost_per_mwh is None:
        if fuel_cost_per_refueling is None:
            fuel_cost_per_mwh = 0.0
        else:
            hours_per_cycle = refueling_cycle_months * 30 * 24
            energy_per_cycle = capacity_mw * capacity_factor * hours_per_cycle
            fuel_cost_per_mwh = fuel_cost_per_refueling / energy_per_cycle

    df = prices.copy().sort_values("timestamp").reset_index(drop=True)
    df["energy_mwh"] = capacity_mw * capacity_factor

    if maintenance_days > 0:
        downtime_hours = int(maintenance_days * 24)
        start = df["timestamp"].iloc[0]
        end_time = df["timestamp"].iloc[-1]
        while start <= end_time:
            mask = (
                (df["timestamp"] >= start)
                & (df["timestamp"] < start + pd.Timedelta(days=maintenance_days))
            )
            downtime_idx = df.index[mask][:downtime_hours]
            df.loc[downtime_idx, "energy_mwh"] = 0.0
            start += pd.DateOffset(months=maintenance_interval_months)

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

    investment_schedule = [annual_investment] * construction_years + [0] * operational_years

    op_cost_schedule = [0] * construction_years
    current_cost = annual_op_cost
    for _ in range(operational_years):
        op_cost_schedule.append(current_cost)
        current_cost *= 1 + op_cost_inflation
    op_cost_schedule[-1] += decommissioning

    # --- Simulate plant operation over the operational period ---
    hours = operational_years * 365 * 24
    timestamps = pd.date_range("2024-01-01", periods=hours, freq="H")
    price_df = pd.DataFrame({"timestamp": timestamps, "price": electricity_price})

    fuel_cost = params.get("fuel_cost_per_mwh")
    fuel_per_refueling = params.get("fuel_cost_per_refueling")
    refuel_months = params.get("refueling_cycle_months", 18)
    maintenance_days = params.get("maintenance_days", 30)

    if fuel_cost is None and fuel_per_refueling is not None:
        hours_per_cycle = refuel_months * 30 * 24
        cycle_energy = capacity_mw * capacity_factor * hours_per_cycle
        fuel_cost = fuel_per_refueling / cycle_energy
    elif fuel_cost is None:
        fuel_cost = 0.0

    _, op_df = simulate_plant_operation(
        price_df,
        capacity_mw=capacity_mw,
        fuel_cost_per_mwh=fuel_cost,
        maintenance_days=maintenance_days,
        capacity_factor=capacity_factor,
        maintenance_interval_months=18,
    )

    op_df["year"] = op_df["timestamp"].dt.year
    energy_by_year = op_df.groupby("year")["energy_mwh"].sum().tolist()
    revenue_by_year = op_df.groupby("year")["revenue"].sum().tolist()

    energy_schedule = [0] * construction_years
    revenue_schedule = [0] * construction_years
    degrade = 1.0
    for e, r in zip(energy_by_year, revenue_by_year):
        energy_schedule.append(e * degrade)
        revenue_schedule.append((r * degrade) / 1_000_000)
        degrade *= 0.999

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
    if energy_by_year:
        print(f"  - First Year Energy Output: {energy_by_year[0]:,.0f} MWh")

    print("\n--- Model Results ---")
    lcoe_dollars = lcoe_result * 1_000_000
    print(f"Levelized Cost of Energy (LCOE): ${lcoe_dollars:,.2f} per MWh")
    print("\nThis LCOE represents the minimum average price at which electricity must be sold")
    print("for the project to break even over its lifetime (i.e., achieve an NPV of zero).")

    npv_result = calculate_npv(net_cash_flows, discount_rate)
    print(
        f"\nNet Present Value (NPV) using simulated operation: ${npv_result:,.2f} Million"
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
    total_profit = op_df["profit"].sum()
    print(
        f"Simulated total profit over {operational_years} years: ${total_profit:,.2f}"
    )

# --- Main execution block with an example scenario ---
def main() -> None:
    params_path = Path(__file__).resolve().parent / "example_plant.json"
    params = load_parameters(params_path)
    print("--- Financial Model for a Hypothetical Nuclear Power Plant ---")
    run_example(params)


if __name__ == "__main__":
    main()
