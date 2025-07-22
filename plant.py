import numpy as np
import numpy_financial as npf

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

# --- Main execution block with an example scenario ---
if __name__ == '__main__':
    print("--- Financial Model for a Hypothetical Nuclear Power Plant ---")

    # --- 1. Define Project Parameters ---
    # These parameters are for a hypothetical plant and can be changed.
    CONSTRUCTION_PERIOD_YEARS = 8
    OPERATIONAL_LIFE_YEARS = 40
    TOTAL_LIFE_CYCLE_YEARS = CONSTRUCTION_PERIOD_YEARS + OPERATIONAL_LIFE_YEARS
    
    DISCOUNT_RATE = 0.08  # 8% discount rate

    # Costs are in millions of USD
    OVERNIGHT_COST_USD_MILLION = 6000 
    ANNUAL_INVESTMENT = OVERNIGHT_COST_USD_MILLION / CONSTRUCTION_PERIOD_YEARS
    
    ANNUAL_OPERATION_COST_USD_MILLION = 150  # Includes fuel, maintenance, etc.
    OP_COST_INFLATION = 0.02  # 2% annual escalation of operating costs
    DECOMMISSIONING_COST_USD_MILLION = 900  # Treated as a final operational cost
    RESIDUAL_VALUE_USD_MILLION = 0 # Assuming no value at the end of life

    # Plant capacity and output
    PLANT_CAPACITY_MW = 1200
    CAPACITY_FACTOR = 0.90 # 90% availability
    ANNUAL_ENERGY_PRODUCTION_MWH = PLANT_CAPACITY_MW * 24 * 365 * CAPACITY_FACTOR

    # --- 2. Prepare Data Arrays based on the formulas ---
    # The arrays represent the full life-cycle of the plant year by year.
    
    # Investment costs (I_t)
    investment_schedule = [ANNUAL_INVESTMENT] * CONSTRUCTION_PERIOD_YEARS + [0] * OPERATIONAL_LIFE_YEARS
    
    # Operational costs (K_t) with escalation
    op_cost_schedule = [0] * CONSTRUCTION_PERIOD_YEARS
    current_cost = ANNUAL_OPERATION_COST_USD_MILLION
    for _ in range(OPERATIONAL_LIFE_YEARS):
        op_cost_schedule.append(current_cost)
        current_cost *= (1 + OP_COST_INFLATION)
    # Add decommissioning cost to the final year
    op_cost_schedule[-1] += DECOMMISSIONING_COST_USD_MILLION

    # Energy production (A_t)
    energy_schedule = [0] * CONSTRUCTION_PERIOD_YEARS
    current_energy = ANNUAL_ENERGY_PRODUCTION_MWH
    for _ in range(OPERATIONAL_LIFE_YEARS):
        energy_schedule.append(current_energy)
        current_energy *= 0.999  # 0.1% degradation per year

    # Net Cash Flow (NCF_t) for NPV calculation
    # For simplicity, we'll estimate revenue to see if the project is profitable at a certain electricity price.
    # Let's test a hypothetical electricity price of $95/MWh
    ELECTRICITY_PRICE_USD_PER_MWH = 95
    revenue_schedule = [0] * CONSTRUCTION_PERIOD_YEARS
    for energy in energy_schedule[CONSTRUCTION_PERIOD_YEARS:]:
        revenue_schedule.append((energy * ELECTRICITY_PRICE_USD_PER_MWH) / 1_000_000)
    
    # NCF = Revenues - (Investments + Operational Costs)
    net_cash_flow_schedule = np.array(revenue_schedule) - (np.array(investment_schedule) + np.array(op_cost_schedule))

    # --- 3. Run Calculations and Display Results ---
    
    # Calculate LCOE
    lcoe_result = calculate_lcoe(
        investment_costs=investment_schedule,
        operation_costs=op_cost_schedule,
        energy_production=energy_schedule,
        discount_rate=DISCOUNT_RATE,
        residual_value=RESIDUAL_VALUE_USD_MILLION
    )
    
    print(f"\nProject Parameters:")
    print(f"  - Discount Rate: {DISCOUNT_RATE:.1%}")
    print(f"  - Total Lifecycle: {TOTAL_LIFE_CYCLE_YEARS} years ({CONSTRUCTION_PERIOD_YEARS} construction + {OPERATIONAL_LIFE_YEARS} operation)")
    print(f"  - Total Investment: ${OVERNIGHT_COST_USD_MILLION:,.0f} Million")
    print(f"  - Annual Energy Output: {ANNUAL_ENERGY_PRODUCTION_MWH:,.0f} MWh")

    print("\n--- Model Results ---")
    # Convert from millions of dollars to dollars per MWh for readability
    lcoe_dollars = lcoe_result * 1_000_000
    print(f"Levelized Cost of Energy (LCOE): ${lcoe_dollars:,.2f} per MWh")
    print("\nThis LCOE represents the minimum average price at which electricity must be sold")
    print("for the project to break even over its lifetime (i.e., achieve an NPV of zero).")

    # Calculate NPV
    npv_result = calculate_npv(
        net_cash_flows=net_cash_flow_schedule,
        discount_rate=DISCOUNT_RATE
    )

    print(f"\nNet Present Value (NPV) at a fixed price of ${ELECTRICITY_PRICE_USD_PER_MWH}/MWh: ${npv_result:,.2f} Million")
    if npv_result > 0:
        print("The project is financially viable under these assumptions, as the NPV is positive.")
    else:
        print("The project is not financially viable under these assumptions, as the NPV is negative.")

    # Calculate IRR
    irr_result = calculate_irr(net_cash_flow_schedule)
    if irr_result is not None:
        print(f"Internal Rate of Return (IRR): {irr_result:.2%}")
    else:
        print("IRR could not be calculated.")

    payback = calculate_discounted_payback_period(net_cash_flow_schedule, DISCOUNT_RATE)
    if payback is not None:
        print(f"Discounted Payback Period: {payback} years")
    else:
        print("Discounted payback period was not reached within the project life.")
