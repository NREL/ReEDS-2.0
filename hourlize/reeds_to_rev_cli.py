"""ReEDS to reV click command line interface"""
import json
import sys
from pathlib import Path
import logging
import shutil
from collections import OrderedDict

import click

import reeds_to_rev

logger = logging.getLogger("reeds_to_rev")

CONTEXT_SETTINGS = {"max_content_width": 9999, "terminal_width": 9999}
REQUIRED_CONFIG_KEYS = {
    "reeds_path": Path,
    "run_folder": Path,
    "reduced_only": bool,
    "tech_supply_curves": dict,
    "constrain_to_bins": bool,
    "priority": dict,
}


def setup_logger(existing_logger, log_level=logging.INFO):
    """
    Sets up pre-existing ``logger`` with with a streamhandler
    and messaging foramtting.
    Parameters
    ----------
    existing_logger : logging.Logger
        Pre-existing logger which will be setup.
    log_level : int, optional
        Logging level. By default logging.INFO (=20). For other valid values
        see https://docs.python.org/3/library/logging.html#logging-levels
    Returns
    Returns
    -------
    logging.Logger
        Configured logger. Note: if your existing_logger is a global,
        this return variable can be discarded.
    """

    existing_logger.setLevel(log_level)
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    stream.setFormatter(formatter)
    existing_logger.addHandler(stream)

    return existing_logger


def add_filehandler(existing_logger, log_dir):
    """
    Adds a FileHanndler to an existing logger. This enables writing of log messages to
    a file named ``reeds_to_rev.log`` in the specified ``log_dir``.
    Parameters
    ----------
    existing_logger : logging.Logger
        Existing logger instance.
    log_dir : pathlib.Path
        Path to directory in which filehandler will write log.
    """
    log_file = log_dir.joinpath("reeds_to_rev.log")
    fh = logging.FileHandler(log_file, mode="w")
    fh.setLevel(existing_logger.handlers[0].level)
    fh.setFormatter(existing_logger.handlers[0].formatter)
    existing_logger.addHandler(fh)


class ConfigError(Exception):
    """
    Custom Exception. Intended to be used for summarizing errors encountered during
    validation of an input Configuration file.
    """


def validate_tech_supply_curves(tech_supply_curves):
    """
    Validate an input "tech_supply_curves" dictionary (e.g., from a configuration JSON).
    Check that for each input key/value pair, the key (which will be interpreted as
    a technology) is in the allowable set of valid technologies and that the value,
    which (which will be interpreted as the path to the supply curve for that tech)
    can be cast to a pathlib.Path.

    Parameters
    ----------
    tech_supply_curves : dict
        Input tech_supply_curves parameter.

    Returns
    -------
    list
        List of errors identified during validation. An empty list indicates no errors.
    """

    errs = []
    if len(tech_supply_curves) == 0:
        errs.append("tech_supply_curves is empty.")
    for tech in tech_supply_curves:
        if tech not in reeds_to_rev.VALID_TECHS:
            errs.append(
                "Invalid tech specified in tech_supply_curves. "
                f"Keys must be one of {reeds_to_rev.VALID_TECHS}"
            )
        else:
            try:
                Path(tech_supply_curves[tech])
            except TypeError:
                errs.append(
                    "Invalid value for {tech}. Could not be cast to pathlib.Path"
                )

    return errs


def validate_priority(priority):
    """
    Validate an input "priority" dictionary (e.g., from a configuration JSON). Check
    that for each input key/value pair, the key (which will be interpreted as a column
    name) is a string and that the value (which will be interpreted as the
    sort order) is a valid option from ``["ascending", "descending"]``.

    Parameters
    ----------
    priority : dict
        Input priority parameter.

    Returns
    -------
    list
        List of errors identified during validation. An empty list indicates no errors.
    """

    allowable_sort_orders = ["ascending", "descending"]

    errs = []
    if len(priority) == 0:
        errs.append("priority is empty.")
    for col_name, sort_order in priority.items():
        if not isinstance(col_name, str):
            errs.append("Invalid column name {col_name}. Must be an instance of str.")

        if sort_order not in allowable_sort_orders:
            errs.append(
                f"Invalid sort order {sort_order}. "
                f"Must be one of {allowable_sort_orders}."
            )

    return errs


def validate_config(config_data):
    """
    Validate configuration file. For use with from_config command.

    Parameters
    ----------
    config_data : dict
        Configuration data (typically loaded from configuration JSON).

    Raises
    ------
    ConfigError
        A ConfigError will be raised under any of the following conditions:
        - a required parameter is missing
        - an invalid/unknown parameter is provided
        - a parameter has a value incompatible with the required type
        - a parameter with nested values does not pass more specific validation
    """

    errs = []
    for parameter, cls_type in REQUIRED_CONFIG_KEYS.items():
        if parameter not in config_data:
            errs.append(f"Missing required parameter: {parameter}")
        else:
            try:
                cls_type(config_data[parameter])
            except TypeError:
                errs.append(
                    f"Invalid input for {parameter}. Could not be cast to {cls_type}."
                )
    for parameter in config_data.keys():
        if parameter not in REQUIRED_CONFIG_KEYS:
            errs.append(
                f"Invalid input parameter {parameter}. "
                f"This is not one of the recognized inputs: {list(config_data.keys())}."
            )

    errs += validate_tech_supply_curves(config_data["tech_supply_curves"])
    errs += validate_priority(config_data["priority"])

    if len(errs) > 0:
        err_message = "\n".join(errs)
        raise ConfigError(
            "Configuration did not pass validation. "
            f"The following errors were found: {err_message}"
        )


def load_config(config_json_path):
    """
    Loads config from JSON file to an OrderedDict, to ensure ordering is maintained
    (especially for "priority" key).

    Parameters
    ----------
    config_json_path : pathlib.Path
        Path to JSON config file.

    Returns
    -------
    collections.OrderedDict
        Configuration as an ordered dictionary.
    """

    with open(config_json_path, "r") as f:
        config = json.load(f, object_pairs_hook=OrderedDict)

    return config


def get_priority_from_config(config, cost_col):
    """
    Gets the priority mapping from the config, substituting the actual cost column
    name for entries of *cost_col*, as needed.

    Parameters
    ----------
    config : collections.OrderedDictionary
        Configuration object.
    cost_col : str
        Name of cost column in supply curve dataset. Will be subtituted for entry of
        *cost_col* if found in the priority mapping.

    Returns
    -------
    collections.OrderedDictionary
        Priority mapping to be used for disaggregation.
    """

    priority = OrderedDict()
    for column, sort_order in config["priority"].items():
        if column == "*cost_col*":
            priority[cost_col] = sort_order
        else:
            priority[column] = sort_order

    return priority


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Flag to turn on debug logging. Default is not verbose.",
)
@click.pass_context
def main(ctx=None, verbose=False):
    """reeds_to_rev command line interface."""
    ctx.ensure_object(dict)

    if verbose:
        setup_logger(logger, logging.DEBUG)
    else:
        setup_logger(logger, logging.DEBUG)


@main.command()
@click.argument(
    "json_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "out_path",
    required=True,
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
)
def from_config(json_path, out_path):
    """
    Disaggregates ReEDS capacity to reV sites using input parameters provided
    via a JSON configuration file. Provides a greater range of options for
    disaggregation than the run command.

    JSON_PATH
        Path to JSON file with input parameters.

    OUT_PATH
        Path to output directory where results will be saved.
        If this does not exist, it will be created. The parent directory must exist.
        If this does exist and it contains outputs from previous execution of this
        command, the existing files will be overwritten.

    \b
    Expected format of input JSON file from JSON_PATH looks like:
    ``
    {
        "reeds_path": "<path to parent ReEDS folder>",
        "run_folder": "<path to specific ReEDS run folder",
        "reduced_only": <true/false> # Use true for reduced outputs, false for full
        "tech_supply_curves": {
            # only include entries for the technologies you want to run
            "upv": "<path to upv supply curve>",
            "wind-ons": "<path to wind-ons supply curve>",
            "wind-ofs": "<path to wind-ofs supply curve>",
            "dupv": "<path to dupv supply curve>",
            "csv": "<path to csv supply curve>"
        },
        "constrain_to_bins": <true/false> # Use true to constrain disaggregation to
                                          # resource bins, false to relax this
                                          # constraint for greater flexibility in the
                                          # disaggregation results.
        "priority": {
            # "priority" defines the columns and sort order (ascending/descending)
            # used to prioritize supply curve project sites during disaggregation.
            "*cost_col*": "ascending"
            "total_lcoe": "ascending"
        }
    }``
    More information about "priority":
     - *cost_col* is a special placeholder that can be used for automatically using the
     applicable cost column used by ReEDS for each technology.
     - Any other value will be interpreted literally as the name of a column in the
     technology supply curve.
     - The example above would prioritize disaggregation within each region, class, and
     (if constrain_to_bins = True) to reV sites with the lowest  *cost_col*, first, then
     break any ties by sorting on total_lcoe.
     - Columns do not need to be costs; any column can be used. For example, to use the
     sites with the most developable area first, one could specify ``priority`` as
     ``{"area_developable_sq_km": "descending"}``.
    """

    logger.info(f"Loading input configuration file {json_path}")
    config = load_config(json_path)
    validate_config(config)

    logger.info("Creating output directory")
    out_path.mkdir(exist_ok=True, parents=False)

    logger.info("Adding log to output directory")
    add_filehandler(logger, out_path)

    logger.info("Copying configuration to the output directory")
    out_config = out_path.joinpath("config.json")
    with open(out_config, "w") as f:
        json.dump(config, f)

    logger.info("Copying source code to output directory")
    source_code_paths = [
        Path(__file__),
        Path(__file__).parent.joinpath("reeds_to_rev.py"),
    ]
    for source_code_path in source_code_paths:
        shutil.copy(source_code_path, out_path)

    for tech, sc_file in config["tech_supply_curves"].items():
        if not reeds_to_rev.check_tech(config["run_folder"], tech):
            logger.warning(
                f"Warning: Technology {tech} is not present in ReEDS outputs. "
                "Skipping disaggregation."
            )
            continue

        logger.info(
            f"Preparing required data to disaggregate built capacity for {tech}."
        )
        if not Path(sc_file).exists():
            raise FileNotFoundError(
                f"Could not find supply curve {sc_file} for {tech}."
            )
        cost_col = reeds_to_rev.get_cost_col(tech, sc_file)
        priority = get_priority_from_config(config, cost_col)
        priority_cols = list(priority.keys())

        reeds_to_rev_data = reeds_to_rev.prepare_data(
            config["run_folder"],
            sc_file,
            tech,
            priority_cols=priority_cols,
        )
        # Save a copy of the input supply curve to the output directory
        reeds_to_rev_data["df_sc_in"].to_csv(
            out_path.joinpath(f"df_sc_in_{tech}.csv"), index=False
        )

        logger.info(f"Disaggregating built capacity to reV sites for {tech}")
        disagg_df = reeds_to_rev.disaggregate_reeds_to_rev(
            priority=priority,
            constrain_to_bins=config["constrain_to_bins"],
            tech=tech,
            **reeds_to_rev_data,
        )

        logger.info(f"Formatting and saving output data for {tech}")
        df_sc_out = reeds_to_rev.format_outputs(
            disagg_df, priority_cols, reduced_only=config["reduced_only"]
        )
        reeds_to_rev.save_outputs(df_sc_out, out_path, tech, config["reduced_only"])

    logger.info("Completed reeds_to_rev!")


if __name__ == "__main__":
    main()
