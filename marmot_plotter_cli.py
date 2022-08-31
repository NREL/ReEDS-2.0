import argparse
import pandas as pd
from pathlib import Path

from marmot.marmot_plot_main import MarmotPlot


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Marmot Plotter CLI""")
    parser.add_argument("model", help="Which model type are you formatting or plotting",
                        choices=['ReEDS', 'ReEDS_India', 'SIIP','PLEXOS'])
    parser.add_argument("scenarios", help="Scenario names", nargs='+', type=str)
    parser.add_argument("model_input_folder",
                        help="PLEXOS/ReEDS solutions folder", type=str)
    parser.add_argument("plot_select_file",
                        help="plot_select_file filepath with set of plots to create",
                        type=str)
    parser.add_argument("-a", "--aggregation", help="Plotting region aggregation", type=str, default='region') 

    parser.add_argument("-sf", "--solutions_folder", help='where to save outputs (defaults to model_input_folder)',
                        type=str, default=None)
    parser.add_argument("-mapf", "--mapping_folder", help='location of mapping files, can be used in place of including long mapping filepaths',
                        type=str, default=None)
    parser.add_argument("-rmf", "--region_mapping", help='region_mapping filepath to map custom regions/zones',
                        type=str, default=pd.DataFrame())
    parser.add_argument("-gnf", "--gen_names", help='gen_names filename/filepath to map generator techs',
                        type=str, default="gen_names.csv")
    parser.add_argument("-ogcf", "--ordered_gen_cat_file", help='ordered_gen_cat_file filename/filepath to set gen stack order and categories',
                        type=str, default="ordered_gen_categories.csv")
    parser.add_argument("-cdf", "--color_dictionary_file", help='color_dictionary_file filename/filepath to to assign to each generator category',
                        type=str, default="colour_dictionary.csv")
    parser.add_argument("-scendiff", "--scenario_diff", help="used to compare 2 scenarios", nargs='+', type=str, default=None)
    parser.add_argument("-zrsub", "--zone_region_sublist", help="subset of regions to plot", nargs='+', type=str, default=None)
    parser.add_argument("-x", "--xlabels", help=" x axis labels for facet plots", nargs='+', type=str, default=None)
    parser.add_argument("-y", "--ylabels", help=" y axis labels for facet plots", nargs='+', type=str, default=None)
    parser.add_argument("-tick", "--ticklabels", help="custom ticklabels for plots (not available for every plot type)", nargs='+', type=str, default=None)
    parser.add_argument("-techsub", "--tech_subset", help="tech subset category to plot (the ticklabels value should be a column in the ordered_gen_categories.csv)", 
                        nargs='+', type=str, default=None)


    args = parser.parse_args()

    if args.solutions_folder is None:
        solutions_folder = args.model_input_folder
    else:
        solutions_folder = args.solutions_folder

    if args.mapping_folder:
        mapping_folder = Path(args.mapping_folder)
        gen_names = mapping_folder.joinpath(args.gen_names)
        ordered_gen_cat_file = mapping_folder.joinpath(args.ordered_gen_cat_file)
        color_dictionary_file = mapping_folder.joinpath(args.color_dictionary_file)

        if isinstance(args.region_mapping, str):
            region_mapping = mapping_folder.joinpath(args.region_mapping)
        else:
            region_mapping = args.region_mapping
    else:
        mapping_folder = None
        gen_names = args.gen_names
        ordered_gen_cat_file = args.ordered_gen_cat_file
        color_dictionary_file = args.color_dictionary_file
        region_mapping = args.region_mapping

    initiate = MarmotPlot(
        args.scenarios,
        args.aggregation,
        args.model_input_folder,
        gen_names,
        ordered_gen_cat_file,
        color_dictionary_file,
        args.plot_select_file,
        marmot_solutions_folder=solutions_folder,
        mapping_folder=mapping_folder,
        Scenario_Diff=args.scenario_diff,
        zone_region_sublist=args.zone_region_sublist,
        xlabels=args.xlabels,
        ylabels=args.ylabels,
        ticklabels=args.ticklabels,
        Region_Mapping=region_mapping,
        TECH_SUBSET=args.tech_subset,
    )

    initiate.run_plotter()
