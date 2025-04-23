#%% Imports
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe
import os
import sys
import argparse
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import reeds
from reeds import plots

plots.plotparams()


#%% Fixed inputs
interactive = False
write = 'png'


#%% Plotting functions
def plot_outage_scheduled(case, f=None, ax=None, color='C0', aspect=1):
    sw = reeds.io.get_switches(case)

    outage_scheduled = reeds.io.get_outage_hourly(case, 'scheduled')

    techs = reeds.techs.get_techlist_after_bans(case)
    techs = [i.split('*')[0] for i in techs if i not in reeds.techs.ignore_techs]

    dfplot = outage_scheduled.loc[
        sw.GSw_HourlyWeatherYears.split('_')[0],
        [c for c in outage_scheduled if c in techs]
    ] * 100

    if (f is None) and (ax is None):
        nrows, ncols, coords = plots.get_coordinates(dfplot.columns, aspect=aspect)

        plt.close()
        f,ax = plt.subplots(
            nrows, ncols, figsize=(ncols*1.7, nrows*1.25), sharex=True, sharey=True,
            gridspec_kw={'hspace':0.5},
        )
    else:
        nrows = ax.shape[0]
        ncols = ax.shape[1]
        _, _, coords = plots.get_coordinates(dfplot.columns, nrows=nrows, ncols=ncols)

    for tech in dfplot:
        ax[coords[tech]].plot(dfplot.index, dfplot[tech], color=color)
        ax[coords[tech]].set_title(
            tech, y=1,
            path_effects=[pe.withStroke(linewidth=2.0, foreground='w', alpha=0.8)]
        )

    ax[-1,0].set_ylabel('Scheduled outage rate [%]', va='bottom', ha='left', y=0)
    ax[-1,0].yaxis.set_major_locator(mpl.ticker.MultipleLocator(10))
    ax[-1,0].yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax[-1,0].xaxis.set_major_locator(mpl.dates.MonthLocator(bymonth=[1,4,7,10]))
    ax[-1,0].xaxis.set_major_formatter(mpl.dates.DateFormatter('%b'))
    ax[-1,0].xaxis.set_minor_locator(mpl.dates.MonthLocator())
    ax[-1,0].set_xlim(dfplot.index[0]-pd.Timedelta('1D'), dfplot.index[-1])
    ax[-1,0].set_ylim(0)
    plots.despine(ax)
    plots.trim_subplots(ax, nrows, ncols, dfplot.shape[1])

    return f, ax, dfplot


#%%### Procedure
if __name__ == '__main__':
    #%% Argument inputs
    parser = argparse.ArgumentParser(
        description='Check inputs.gdx parameters against objective_function_params.yaml',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('case', help='ReEDS-2.0/runs/{case} directory')
    args = parser.parse_args()
    case = args.case

    # #%% Inputs for testing
    # reeds_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
    # case = os.path.join(reeds_path, 'runs', 'v20250312_scheduledM0_Pacific')
    # interactive = True

    #%% Create output container
    if write.strip('.') == 'png':
        savepath = os.path.join(case, 'outputs', 'maps', 'inputs')
        os.makedirs(savepath, exist_ok=True)

        def saveit(savename):
            plt.savefig(
                os.path.join(savepath, savename.lower().replace(' ', '-') + '.png')
            )
            if interactive:
                plt.show()

    elif write.strip('.') in ['ppt', 'pptx']:
        raise NotImplementedError(f"write={write}")


    #%% Plots
    try:
        f, ax, df = plot_outage_scheduled(case)
        saveit('outage_scheduled')
    except Exception:
        print(traceback.format_exc())
