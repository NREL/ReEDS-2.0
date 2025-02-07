# Retail rate module

This module can be used after finishing a ReEDS run to calculate retail electricity rates by state and year,
where each state is served by its own investor-owned utility (IOU). The retail rate (in ¢/kWh) is given by 
the revenue target for the state IOU divided by the annual retail electricity demand within the state, 
where the revenue target is given by the sum of operating expenses, the return to capital, and income taxes.

This module translates projected generation and transmission capacities and costs from ReEDS into IOU 
balance sheet expenditures, accounting for the distinction between operational and capitalized (or 
“rate-based”) expenditures, depreciation schedules, taxes, and other components. Distribution, 
administration, and intra-regional transmission costs are projected forward based on empirical trends over 
the past decade. 

Additional information about this module can be found here:
Brown, Patrick R, Pieter J Gagnon, J Sean Corcoran, and Wesley J Cole. 2022. Retail Rate Projections for 
Long-Term Electricity System Models. Golden, CO: National Renewable Energy Laboratory. NREL/TP-6A20-78224.
https://www.nrel.gov/docs/fy22osti/78224.pdf. 

## Usage

* `cd` to the REEDS-2.0/postprocessing/retail_rate_module directory
* Run the retail_rate_calculations.py script, with the name of a run folder as a required argument input. For example:
    * `D:\username\ReEDS-2.0\postprocessing\retail_rate_module> python retail_rate_calculations.py v20200806_retailtest_MidCase`

## Outputs

All outputs are written to the `outputs/retail/` folder within the provided run folder. Outputs include:
* `retail_rate_components.csv`: All monetary values are in 2004 dollars. To obtain the retail rate, divide the sum of the cost columns by the 'retail_load' column.
* `costs_over_time.html`: Summary plots for national rates.

## Caveats
* The plotting portion of the script will currently fail if technologies are built that are not in the `map_i_to_tech.csv` file. The main `retail_rate_components.csv` file will still be produced as usual; this error only affects the production of the `costs_over_time.html` summary plots.
* The plots created by the retail rate module will often show certain components of the retail rate dip below the "zero" line. This is due to the order that the module plots each retail rate component when creating stacked bars of the plot: negative-value components are plotted first, then positive-values components are plotted over the negative values, starting at the final value 
of the negative-value components.
For example, if the sum of negative-value components is -$3 and the first positive-value component is $0.25, then the positive-value component will be plotted as a bar from -$3 to -$2.75. The second positive-value component will then be plotted starting at -$2.75. These component plots, then, are primarily used to understand the fractional contribution of each positive-value component of the retail rate module to the overall retail rate over time (the overall retail rate can be found by reading the top of each stacked bar).

## Accounting approach
Here we describe the accounting methods that we employ to translate yearly costs into estimates of the 
revenue to be collected from retail customers through electric bills. This approach is a simplified version 
of actual accounting practices for IOUs in the US.

The retail rates provided by this module consist of two primary components:
* Annual retail electricity demand, which is an exogenously defined, static input to the ReEDS model
* Annual revenue target, which is the amount of revenue that an IOU would collect from ratepayers to cover its costs while achieving a target return to capital

Cost components include capital expenditures (CAPEX) and operational expenditures (OPEX) for generation, 
transmission, distribution, and administration; inter-regional trades; and taxes. These costs are grouped 
into three categories: operational expenses, return to capital, and income taxes.

### Operational expenses
Operating expenses include all generation, distribution, transmission, and administrative OPEX, the 
depreciation of capital assets, and the costs of inter-state trading. For all of these expenses, we assume 
that each year's expense is directly passed through to ratepayers during the year in which it is incurred.

Operating expenses are equal to the sum of:
* Operations expenses
* Non-capitalized maintenance expenses
* Depreciation expenses
* Expenses incurred by purchasing power and other services

### Return to capital
The return to capital is the compensation to shareholders and debtholders. It is driven primarily by an 
IOU's rate base, which consists of the total net plant in service, plus working capital, minus any 
accumulated deferred income taxes, described here: 
* __Net plant in service__: Every capital asset has a net plant in service dollar value, where “plant” is a 
generic reference to a capital asset. A capital asset’s net plant in service is the original book value of 
the capital asset, minus the accumulated depreciation for that capital asset up to that point. Once a 
capital asset has fully depreciated its book value, it no longer contributes to the rate base. 
    * In  our implementation, the original plant investment, ongoing capitalized maintenance expenses, 
    retrofits, and rebuilds are all tracked as separate investments and can have their own depreciation 
    schedules if warranted.
* __Working capital__: Working capital is the net value of current assets minus current liabilities that 
the utility needs to conduct its operations — for example, the value of on-site fuel stocks and cash 
balances to manage day-to-day expenses. 
    * We estimate the total amount of working capital as the equivalent of 45 days of all operating 
    expenses (i.e., 45/365 × annual operating expenses). 
* __Accumulated deferred income taxes (ADIT)__: ADIT is the total value of any deferred income taxes, e.g., 
from using a faster depreciation schedule for tax purposes than was used for calculating annual 
depreciation expenses. 

We assume that the rate base represents the total amount of capital required by the IOU, which is 
composed of both debt and equity. We calculate how much equity and debt are required according to the 
following equations: 

* `Return to equity` = `rate base` * `equity fraction` * `equity rate of return` 
* `Return to debt` = `rate base` * `debt fraction` * `interest rate` 

### Income taxes
In practice, a corporation would calculate their net income to determine their income tax burden. However, 
we make the assumption that the only class of revenue collection that is not exactly offset by an equal 
expense is the return to equity, which greatly simplifies our accounting.

With this assumption, we start with the year’s calculated return to equity, explained above, and subtract 
any income tax credits claimed that year. Then we use the following equation, where _T_ is the effective 
tax rate, to calculate the additional amount of revenue that would need to be collected and directed 
towards income taxes to maintain the target return to capital while also covering costs:

(`return to equity` - `income tax credits`) * (${1 \over 1 - T} - 1$)

## Cost components
### Generation
Generation CAPEX is derived from two sources: 
* Historical capacity built from 2010–2019 and projected capacity built from 2020–2050 is provided by the ReEDS model, with annual cost assumptions taken from the ATB. 
* Capacity and construction dates before 2010 are taken from the EIA NEMS database. As a simplifying assumption, ReEDS/ATB technology-specific CAPEX cost assumptions for 2010 are applied to all capacity built before 2010

Generation OPEX includes multiple components, all derived from ReEDS model outputs: 
* Fixed operations and maintenance (FOM)
* Fuel
* Variable operations and maintenance (VOM)
* Operating reserves
* Alternative compliance payments (ACP) for state renewable portfolio standards

FOM costs are separated into capitalized and non-capitalized costs, which are treated separately in the 
accounting procedure detailed above. Capitalized costs include, for example, capital assets whose costs are 
recovered through depreciation over time, such as module replacement for a PV plant or boiler replacement 
for a thermal plant. Non-capitalized costs are expenses that are not capital assets, such as maintenance 
labor.

### Transmission
Transmission capacity includes spur lines for wind and solar generators, substations, inter-BA transmission 
lines, and intra-BA transmission.

Transmission CAPEX is derived from several sources:  
* Spur line costs for candidate wind and solar sites are calculated in the Renewable Energy Potential (reV) 
model and used as inputs to ReEDS; spur line costs for constructed sites are then obtained from ReEDS 
outputs. 
* Inter-BA transmission capacity is obtained from ReEDS projections. The cost of each inter-BA line is 
evenly split between the BAs it connects. 
* Inter-BA transmission lines incur an additional, voltage-dependent substation cost, drawing from a supply 
curve of available substation capacity and cost by voltage within each BA. 
* Intra-BA transmission capacity and cost (aside from wind/solar spur lines and substations) are not 
directly modeled in ReEDS. Intra-BA transmission costs are estimated using from the ABB Velocity Suite 
database of Federal Energy Regulatory Commission (FERC) Form 1 responses from 2010–2019.

Existing transmission capacity is assumed to have been built uniformly over the previous 40 years using the 
same cost ($/kW-km) as new transmission in ReEDS.

Annual transmission OPEX is similarly taken from FERC Form 1 responses.

### Distribution & Administration
Distribution and administration CAPEX are taken from the “Electric Plant in Service” schedule of FERC Form 
1.
Distribution and administration OPEX are taken from the “Electric Operation and Maintenance Expenses” 
schedule schedule of FERC Form 1.

The data in FERC Form 1 are not comprehensive; for some states (particularly those with a greater 
proportion of demand served by non-IOU entities), the data reported by IOUs in FERC Form 1 represent a 
small fraction of total retail demand in the state. Therefore, we calculate the ¢/kWh rate contributions 
for distribution CAPEX and OPEX, administration CAPEX and OPEX, and transmission OPEX by aggregating the 
data in FERC Form 1 across IOUs at three different levels of aggregation (state, region, and nation), 
calculating the complete retail rate for each state, and comparing the calculated state retail rate in 
2010–2019 to the historical annual state retail rate reported in EIA Form 861. The aggregation level 
(state, region, or nation) that minimizes the mean bias error (MBE) over 2010–2019 for each state is then 
used when calculating ¢/kWh rate contributions for distribution CAPEX/OPEX, administration CAPEX/OPEX, and 
transmission OPEX.

### Interregional expenditure flows and tax credits
Inter-BA flows and accompanying expenses are tracked for energy, operating reserves, planning reserves, and 
RPS credits. Energy flows are also tracked between Canada and adjacent BAs in the US. Inter-regional 
expenditure flows are treated as operating expenditures in the importing BA and credits in the exporting 
BA, increasing the revenue target (and associated retail rate) in the importing BA and reducing the revenue 
target in the exporting BA.

Federal tax credits reduce generation CAPEX/OPEX expenditures, thereby reducing utility expenditures and 
associated revenue targets and retail rates. The cost to the federal government of these tax incentives is 
not included in the rates reported here.
