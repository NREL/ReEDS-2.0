# %% ===========================================================================
### --- IMPORTS ---
### ===========================================================================

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.colors as mcolors


# %% ===========================================================================
### --- FUNCTIONS ---
### ===========================================================================

"""

Example of how to call script: python reg_cap_cost_plot.py /Users/kminderm/ReEDS-2.0

"""

def get_tech_mapping(reedspath, tech):
    tech_subsets = pd.read_csv(
        os.path.join(reedspath, "inputs", "tech-subset-table.csv"), index_col=0
    )

    # tech name mappings
    name_mappings = {
        "batteries": "BATTERY",
        "biomass": "BIO",
        "coal_noccs": "COAL",
        "coal_ccs": "COAL_CCS",
        "gas_cc": "GAS_CC",
        "gas_ct": "GAS_CT",
        "nuclear": "NUCLEAR",
        "pv": "PV",
        "wind_ons": "ONSWIND",
        "wind_ofs": "OFSWIND",
    }

    # get techs that should be plotted
    if tech in ["batteries", "wind_ons", "wind_ofs"]:
        return [name_mappings[tech]]
    else:
        return tech_subsets.index[tech_subsets[name_mappings[tech]] == "YES"].tolist()


def create_plot(subset_gdf, tech):
    # Tech/title mapping
    plot_titles = {
        'batteries': 'Batteries',
        'biomass': 'Biomass',
        'coal_noccs': 'Coal (no CCS)',
        'coal_ccs': 'Coal (with CCS)',
        'gas_cc': 'Natural Gas Combined Cycle',
        'gas_ct': 'Advanced Gas Combustion Turbine', 
        'nuclear': 'Nuclear', 
        'pv': 'Photovoltaic', 
        'wind_ons': 'Land-based Wind',
        'wind_ofs': 'Offshore Wind'
    }

    vmin = 0.8254
    vmax = 1.3385

    # set 1.0 to be the middle of the color scale.
    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)

    ## create one plot
    fig, ax = plt.subplots(1, 1)
    subset_gdf.plot(
        ax=ax,
        column="reg_cap_cost_mult",
        cmap='coolwarm',
        norm=norm,
        legend=True,
        edgecolor="black",
        linewidth=0.3,
    )

    # other plotting configuration
    ax.set_title(f"{plot_titles[tech]}", fontsize=14)
    ax.axis("off")

    return fig, ax


def main(path):
    reedspath = path

    # Map between regions and states
    hierarchy = pd.read_csv(os.path.join(reedspath, "inputs", "hierarchy.csv"))
    hierarchy = hierarchy.loc[hierarchy.country == "USA"]
    hierarchy = hierarchy.set_index("ba")

    # Get regional capital cost multipliers
    df = pd.read_csv(
        os.path.join(reedspath, "inputs", "financials", "reg_cap_cost_mult_default.csv")
    )

    # Pull in the BA region shapefile
    reeds_gdf = gpd.read_file(
        os.path.join(reedspath, "inputs", "shapefiles", "US_PCA", "US_PCA.shp")
    ).rename(columns={"rb": "r"})

    # Combine the two dfs to get geographic shape properties
    dfmap = reeds_gdf.merge(df, how="inner", on="r")

    # Create directory to save plots if it doesn't exist
    output_path = os.path.join(reedspath, 'docs', 'source', 'plotting_scripts', 'reg_cap_cost_plots') 
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # List of techs to plot
    techs = [
        "batteries",
        "biomass",
        "coal_noccs",
        "coal_ccs",
        "gas_cc",
        "gas_ct",
        "nuclear",
        "pv",
        "wind_ons",
        "wind_ofs",
    ]

    # Create plots for each technology and save
    for t in techs:
        print(f"Plotting regional capital costs for {t}")
        tech_mapping = get_tech_mapping(reedspath, t)
        subset_gdf = dfmap[dfmap["i"].isin(tech_mapping)]

        # get the plot
        fig, ax = create_plot(subset_gdf, t)
        fig.savefig(
            os.path.join(output_path, f"{t}_reg_cap_cost.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)

    print(f"Plots can be found in {output_path}")


if __name__ == "__main__":
    reedspath = sys.argv[1]

    main(reedspath)