# H2 inputs 

## consume_char_[GSw_H2_Inputs].csv

Contains cost and performance assumption for electrolyzers and steam-methane reformer.

Electrolyzer capital cost assumptions are based on the Pathways to Commercial Liftoff: Clean Hydrogen Report (https://liftoff.energy.gov/wp-content/uploads/2023/05/20230320-Liftoff-Clean-H2-vPUB-0329-update.pdf) [see values in the footnotes of Figure 3 on page 14]. The reference scenario assumes linearly decline from 1750 $/kW in 2022 to 550 $/kW in 2030, and then remain constant after. The low cost scenario assumes further declines from 2030 to 2050. 

Fixed O&M values are assumed to be 5% of CAPEX (source: https://iopscience.iop.org/article/10.1088/1748-9326/acacb5)

Electrolyzer performance (efficiency) as well as SMR cost and performance assumptions are derived from assumptions H2A: Hydrogen Analysis Production Models (https://www.nrel.gov/hydrogen/h2a-production-models.html), with guidance from Paige Jadun. See original input assumptions in the ReEDS-2.0_Input_Processing repo: https://github.nrel.gov/ReEDS/ReEDS-2.0_Input_Processing/blob/main/H2/costs/H2ProductionCosts-20210414.xlsx.

Note that SMR costs are currently in 2018$ and electrolyzer costs are in 2022$.

## h2_transport_and_storage_costs.csv

| Investment    | Cost type | Units |
| ------------- | ------------- | ------------- |
| Pipelines  | Overnight Capital Cost  | $/[(metric ton/hour)*mile] |
| Pipelines  | FOM  | $/[(metric ton/hour)*mile*year] |
| Pipelines  | Electric load | MWh/metric ton |
| Compressors  | Overnight Capital Cost  | $/(metric ton-hour) |
| Compressors  | FOM  | $/[(metric ton/hour)*year) |
| Compressors  | Electric load  | MWh/metric ton |
| Storage  | Overnight Capital Cost  | $/metric ton |
| Storage  | FOM  | $/(metric ton*year) |
| Storage  | Electric load  | MWh/metric ton |

The values in `H2_transport_and_storage_costs.csv` are based on raw data provided from the SERA model by Paige Jadun. The raw data are formated by the `process-h2-inputs.py` script in the input processing repository (https://github.nrel.gov/ReEDS/ReEDS-2.0_Input_Processing/blob/main/H2/process-h2-inputs.py).

## Intra-Regional Hydrogen Transport Cost
Flat cost for intra-ReEDS BA hydrogen transport and storage in $/kg H2 produced. Specified via `GSw_H2_IntraReg_Transport`. Default value assumes transport via pipelines and is from [2023 DOE Clean Hydrogen Liftoff Report](https://liftoff.energy.gov/wp-content/uploads/2023/05/20230523-Pathways-to-Commercial-Liftoff-Clean-Hydrogen.pdf) pg 15. Transport costs could be more expensive if you assume other methods of H2 transport (ex. trucking). 

Note: this cost is only assessed for new plants (those that fall in the `newv(v)` set), not existing H2 producers. This is because existing hydrogen plants likely have already installed the necessary infrastructure to connect to a hydrogen demand center (likely an industrial plant) and that infrastructure was likely sized appropriately for the consumers needs. Therefore, that H2 producer shouldn't pay an additional investment cost for intra-regional hydrogen transport since they will not be transporting hydrogen elsewhere. However, new hydrogen producing plants, especially in a decarbonized power system or if a large hydrogen economy manifests, might not be physically close to the hydrogen consumers and therefore should pay this cost.

## h2_storage_rb.csv

Mapping of ReEDS balancing are to available H2 storage type. Since costs are always ordered (saltcavern < hardrock < above ground), BAs with access to saltcaverns or hardrock storage are only assigned to the cheapest option to reduce the model size.

## Retail adder for electrolytic load
- One option for the retail adder for electrolytic load (`GSw_RetailAdder`) is derived from the difference between the industrial average rate and the ReEDS wholesale cost. The calculation below is done in 2023 dollars:
    - National average energy price paid in 2023 by industrial consumers (via EIA 861, https://www.eia.gov/electricity/data/eia861m/ --> sales and revenue --> download data. This value is the sales weighted average): $80.55/MWh
    - ReEDS average wholesale cost from 2023 Standard Scenarios Mid-case in model 2026 (since we cannot find quality empirical wholesale prices): $41.78/MWh
    - Difference between the industrial average rate and the wholesale cost: $39/MWh
    - Deflated to 2004 dollars: $28/MWh

Note: please be aware that ReEDS's solutions are very sensitive to this switch. With `GSw_RetailAdder=28`, there is very little to no electrolytic hydrogen. With `GSw_RetailAdder=0` and with exogenous H2 demand, you may see nearly all of the exogenous H2 demand profile being met by electrolyzers and/or a large endogenous H2 economy.

# Hydrogen Production Tax Credit (45V)

# The regulation itself
The hydrogen production tax credit was enacted in the Inflation Reduction Act in 2022. It is commonly referred to as 45V due to the section of the tax code it is in. It provides up to $3 per kg of H2 produced (2022 USD, credit amount is [inflation adjusted in subsequent years](https://www.taxnotes.com/research/federal/irs-guidance/notices/irs-releases-clean-hydrogen-credit-inflation-adjustment/7kd80)), based on the lifecycle emissions of hydrogen production as shown in the table below. These lifecycle greenhouse gas emissions only includes emissions only through the point of production (i.e. does not include hydrogen transport or storage). 

Since the largest component of the lifecycle emissions of electrolytic hydrogen production is the carbon intensity of the generators powering the electrolyzer, the main point of contention for this regulation has been how to define the carbon intensity of electricity. The Department of the Treasury proposed [guidance](https://www.federalregister.gov/documents/2023/12/26/2023-28359/section-45v-credit-for-production-of-clean-hydrogen-section-48a15-election-to-treat-clean-hydrogen) on December 22, 2023 stating the requirements for demonstrating the CO2 intensity of H2 production and published their [final rules](https://www.federalregister.gov/public-inspection/2024-31513/credit-for-production-of-clean-hydrogen-and-energy-credit) on January 3, 2025. This press release has a nice [summary](https://home.treasury.gov/news/press-releases/jy2768).

| Life-cycle Emissions (kg CO2-e / kg H2) | PTC (2022$ / kg H2) | CO2 intensity of electricity to meet incentive required through electrolysis (tonnes CO2 / MWh) |
| --------------- | ---------- | --------------- |
| [4, 2.5]  | 0.6 | [.07, .045] |
| (2.5, 1.5] | 0.75 | (.045, .027]  |
| (1.5, 0.45] | 1 | (.027, .007] |
| (0.45, 0] | 3 | (.008, 0] |

To ensure the low carbon intensity of the electricity powering electrolyzers, the hydrogen production tax credit has three "pillars" or core components, as described below:  
1. Incrementality (also referred to as additionality): generators must have a commercial online date no more than three years before a H2 production facility's placed in service date to qualify. Example: if an electrolyzer is put in service in 2028, only generators whose commercial operations dates are between 2025-2028 may qualify to power this electrolyzer. This requirement starts immediately. There are special exceptions for nuclear, CCS and states with robust GHG emission caps - we do not model these additional pathways in ReEDS. 
2. Hourly matching: each MWh must be consumed by an electrolyzer in the same hour of the year in which it was generated.
3. Deliverablity: each MWh must be consumed by an electrolyzer in the same region in which it was generated. Regional matching is required at the National Transmission Needs Study region level, as shown in the image below. 

![image](https://media.github.nrel.gov/user/2165/files/d7b3e8ae-cb0c-4413-8442-4e6b720bcd20)

Source: [Guidelines to Determine Well-to-Gate GHG Emissions of Hydrogen Production Pathways using 45VH2-GREET 2023](https://www.energy.gov/sites/default/files/2023-12/greet-manual_2023-12-20.pdf), 2023, Figure 2

These three pillars are combined differently depending on which year it is:
- 2024-2029: annual matching, regional matching, additionality required
- 2030 onwards: hourly matching, regional matching, additionality required

Please see the Department of the Treasury [final rules](https://www.federalregister.gov/public-inspection/2024-31513/credit-for-production-of-clean-hydrogen-and-energy-credit) if you want to learn more.

## How is this regulated? 
There will be a system of trading credits, which are called Energy Attribute Credit (EACs). This is similar to Renewable Energy Credits (RECs). Qualifying clean technologies produce EACs which are tracked by region, vintage (commercial online year), and hour in which they are produced. Electrolyzers must purchase and retire EACs for all MWh used in order to receive the 45V credit.

## Which generating technologies qualify to produce Energy Attribute Credits?
The law is technology neutral and does not stipulate which technologies can or cannot produce an EAC, it only specifies the lifecycle emissions of hydrogen production, which is calculated by the [GREET Model](https://www.anl.gov/topic/greet) out of Argonne National Lab. This model considers the carbon intensity of the electricity from various sources. You can reverse calculate the range of CO2 intensity of electricity required to meet the various incentive levels (assuming H2 production via electrolysis). These are the values in the 3rd column of the table above. Based on their low CO2 emissions, qualifying clean technologies could include: wind, solar PV, nuclear, gas with CCS, geothermal and hydropower.

## What years does the hydrogen production tax credit apply to?
The hydrogen production tax credit took effect immediately, so in 2023. Projects must begin construction by 2033. The credit can be received for 10 years. Therefore, the latest we would see plants receiving 45V through 2042. If the final regulations include a 4-hr year safe harbor (consistent with other tax credits such as the PTC and ITC), then projects receiving 45V could consutrction as late as by 2037 and receive 45V through 2046.

## Intersection with other tax credits and policies:
- Section 45Y PTC and Section 48E ITC 
   - 45V can be stacked with the PTC/ITC. This is because it is two different plants which are claiming the credit. Example: a wind plant could produce a MWh of energy and receive the generation PTC for that energy produced. That energy could power an electrolyzer which could then receive 45V.
- Section 45Q - carbon capture and sequestration
    - The same plant cannot claim both 45Q and 45V. So for example, an SMR-CCS plant cannot claim both 45Q for their carbon capture and 45V for their hydrogen production. They must choose one. We calculated that 45Q will be most valuable for most SMR-CCS plants and therefore assume that they take that in the model.
    - However, a gas-CCS plant could produce a MWh of energy and receive 45Q for that energy produced. Since they are a relative clean generator per their lifecycle emissions, this energy produces a EAC. So the gas-CCS plant would receive 45Q and the electrolyzer would receive 45V. People frequently confuse this. Only the hydrogen producer receives 45V. Generating technologies are merely creating the Energy Attribute Credit which hydrogen producers need to prove that their electricity is "clean enough".
- RECs
   - A generating technology can choose to produce a REC or an EAC, but not both. 

## Implementation in ReEDS

- Qualifying clean technologies produce Energy Attribute Credits (EACs, similar to the REC system) which are tracked by region (h2ptcreg), vintage (commercial online year), and hour in which they are produced.
    - Qualifying clean technologies include: wind, solar PV, nuclear, gas with CCS, geothermal, hydropower
    - These are defined by the set i_h2_ptc_gen(i) and carried through the model as valcap_h2ptc and valgen_h2ptc
- Electrolyzers must purchase and retire EACs for all MWh used in order to receive the 45V credit
    - This is accomplished via the new variable CREDIT_H2PTC(i,v,r,allh,t)
- Pre-2030 those EACs can be generated at any time within the year the H2 is generated; 2030 and later the EACs must be matched hourly
- Simplifying assumption used for vintage: generators must have a commercial online date in 2024 or later in order to qualify as an EAC producer
    - Applied by restricting valcap_h2ptc to have firstyear_v(i,v)>=h2_ptc_firstyear


### Assumptions
- We only represent technologies which qualify for the less than 0.45 kg CO2e/kg H2 lifecycle emissions category. There may be relatively clean generators that qualify for lower $ amounts of the PTC. However, since the $3/kg is so lucrative, it is assumed that all H2 producers will comply with the mechanisms required to prove the cleanliness of their electricity.
- This PR consists of only grid-connected electrolyzers. We did not include off grid systems due to insufficient evidence of their BOS costs, logistical tractability and more. However, there may be off-grid systems which are cost competitive with grid connected systems.
- SMR with CCS could technically receive the H2 PTC. However, our back of the envelope calculations show that SMR w/ CCS plants are more likely to take 45Q so that is why ReEDS currently assumes that only electrolyzers take the H2 PTC. 
- We force all electrolyzers to take 45V, and therefore we force there to be 45V-credited generation if there is electrolyzer load. Our logic was that for an electrolyzer to be cost competitive with SMR or SMR-CCS, it would need and want to take the $3/kg 45V. This assumption is enforced by the constraints `eq_h2_ptc_region_balance` and `eq_h2_ptc_region_hour_balance`.

### Recommended switches to incorporate the hydrogen production tax credit into a run.
| Switch | Value | Recommend or Required for running with the H2 PTC enabled | Function |
| -- | -- | -- | -- |
| GSw_H2_PTC | 1 | Required | Turns on and off hydrogen production tax credit  |
| GSw_H2 | 2 | Recommended | Representation of hydrogen supply/demand balance. Sw_H2=1 will not cause the model to fail but it is not recommended for the most accurate representation of the H2 PTC.  |
| GSw_H2_Demand_Case | Anything except 'none' | Recommended |  Annual H2 demand profile  |
| GSw_H2_IntraReg_Transport | 0.32 | Recommended | Flat cost for intra-ReEDS BA hydrogen transport and storage in $2004 / kg H2 produced. Note: This is now included as the default representation even if the H2 PTC is not enabled. This is assuming transport via pipelines. Transport costs could be more expensive if you assume other methods of H2 transport (ex. trucking).  |
| GSw_RetailAdder  | $0/MWh | Recommended | 2004$/MWh adder to the cost of energy consumed by hydrogen producing facilities and direct air CO2 capture facilities. Included to represent the non-bulk-power-system costs of increasing electrical loads that are not captured within ReEDS. The default value of 0 indicates an assumption that these facilities are large enough to participate directly in wholesale markets.  |

### Other Notes
- The final version of the regulation will not be published until later in FY24, at which point this documentation will be updated to reflect the final regulations.
- Fun fact: There is an Investment Tax Credit (ITC) component to 45V. However, all analyses (both ours and from other research groups) indicate that hydrogen producing facilties will choose to take the H2 PTC so in ReEDS we exclusively model the PTC. 
