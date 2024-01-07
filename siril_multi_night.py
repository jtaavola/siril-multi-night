"""
Process multiple nights in Siril

Exports:
process - process multiple sessions using a Siril calibration script and a Siril stacking script
"""
import os
import shutil
import re
import sys

from pysiril.siril import Siril
from pysiril.wrapper import Wrapper


class _SirilContext:
    """Context manager for using Siril"""

    def __init__(self):
        self.siril = Siril()
        self.cmd = Wrapper(self.siril)

    def __enter__(self):
        self.siril.Open()
        return self.siril, self.cmd

    def __exit__(self, *_):
        self.siril.Close()


class _SirilCd:
    """
    Context manager for changing directories in Siril

    Parameters:
    working_dir -- the path to the working directory for executing Siril commands
    cmd_wrapper -- the Siril command wrapper instance
    """

    def __init__(self, working_dir: str, cmd_wrapper: Wrapper):
        self.working_dir = _abspath(working_dir)
        self.cmd_wrapper = cmd_wrapper
        self.saved_path = ""

    def __enter__(self):
        self.saved_path = os.getcwd()
        self.cmd_wrapper.cd(self.working_dir)

    def __exit__(self, *_):
        self.cmd_wrapper.cd(self.saved_path)


def _abspath(path: str):
    # handles paths with ~ (home)
    expanded_home_path = os.path.expanduser(path)
    return os.path.abspath(expanded_home_path)


def _write_conversion_file(conversion_map: dict[str, str], output_path: str):
    """
    Write a conversion file that lists the mappings of the old and new file paths

    Parameters:
    conversion_map -- a map where the key is the original file path, and the value is the new path
    output_path -- the path to the directory the conversion file will be written too
    """
    conversion_file_path = os.path.join(output_path, "conversion.txt")

    with open(conversion_file_path, "w", encoding="utf-8") as conversion_file:
        for original, output in conversion_map.items():
            conversion_file.write(f"'{original}' -> '{output}'\n")


def _merge_sessions(
    session_paths: list[str],
    output_path: str,
    process_dir: str,
    seq_name: str,
):
    """
    Merge preprocessed lights together from each session. Each session must already be calibrated
    with the `process_dir` populated. The `process_dir` must be a directory inside the session path
    directory.

    Parameters:
    session_paths -- the paths to each session directory
    output_path -- the path to the output directory
    process_dir -- the name of the process directory
    seq_name -- the sequence name of the preprocessed light files
    """
    output_abs_path = _abspath(output_path)

    merge_conversion_map: dict[str, str] = {}
    # counter for the new merged sequence
    seq_index = 1

    for session_path in [_abspath(p) for p in session_paths]:
        session_process_path = os.path.join(session_path, process_dir)

        pp_light_matcher = re.compile(rf"^{seq_name}_.*\.fit")

        # iterate over the preprocessed light files from the process directory
        for pp_light_path in [
            os.path.join(session_process_path, f)
            for f in os.listdir(session_process_path)
            if pp_light_matcher.match(f)
        ]:
            # re-index output file with leading zeros
            output_pp_light_path = os.path.join(
                output_abs_path, f"{seq_name}_{seq_index:05}.fit"
            )

            shutil.copyfile(pp_light_path, output_pp_light_path)
            merge_conversion_map[pp_light_path] = output_pp_light_path
            seq_index += 1

    _write_conversion_file(merge_conversion_map, output_abs_path)


def process(
    session_paths: list[str],
    output_path: str,
    siril_calibrate_script_path: str,
    siril_stack_script_path: str,
    process_dir: str = "process",
    seq_name: str = "pp_light",
):
    """
    Process multiple sessions using Siril. Each session will be calibrated individually with
    `siril_calibrate_script_path`. The preprocessed lights will then be merged together into the
    `output_path` directory. Finally, the merged session data will be registered and stacked with
    `siril_stack_script_path`.

    Parameters:
    session_paths -- the paths to each session directory
    output_path -- the path to the output directory
    siril_calibrate_script_path -- the path to the Siril calibration script
    siril_stack_script_path -- the path to the Siril stacking script
    process_dir -- the name of the process directory (default: "process")
    seq_name -- the sequence name of the preprocessed light files (default: "pp_light")
    """
    output_abs_path = _abspath(output_path)
    if not os.path.exists(output_abs_path):
        os.mkdir(output_abs_path)

    stdout = sys.stdout
    log_file_path = os.path.join(output_abs_path, "siril-mulit-night.log")
    with open(log_file_path, "w", encoding="utf-8") as sys.stdout:
        with _SirilContext() as [siril, cmd_wrapper]:
            # calibrate each session individually
            for session_path in session_paths:
                print(f"Calibrating session: {session_path} ...", file=stdout)
                siril_calibrate_script_abs_path = _abspath(siril_calibrate_script_path)
                with _SirilCd(session_path, cmd_wrapper):
                    siril.Script(siril_calibrate_script_abs_path)

            # merge sessions together
            print("Merging sessions together ...", file=stdout)
            _merge_sessions(session_paths, output_path, process_dir, seq_name)

            # register and stack
            print("Stacking merged sessions ...", file=stdout)
            siril_stack_script_abs_path = _abspath(siril_stack_script_path)
            with _SirilCd(output_path, cmd_wrapper):
                siril.Script(siril_stack_script_abs_path)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="""
        Process multiple nights in Siril
        """
    )
    parser.add_argument(
        "--sessions",
        nargs="+",
        dest="input_sessions",
        help="the list of paths to the sessions of data",
        metavar="",
        required=True,
    )
    parser.add_argument(
        "--calibrate-script",
        dest="input_calibrate_script",
        help="the path to the Siril calibration script",
        metavar="",
        required=True,
    )
    parser.add_argument(
        "--stack-script",
        dest="input_stack_script",
        help="the path to the Siril stacking file",
        metavar="",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="input_output",
        help="the path to the output directory",
        metavar="",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--process-dir",
        dest="input_process_dir",
        help="the name of the Siril process directories",
        metavar="",
        required=False,
        default="process",
    )
    parser.add_argument(
        "--seq-name",
        dest="input_seq_name",
        help="the sequence name of the preprocessed light files",
        metavar="",
        required=False,
        default="pp_light",
    )

    args = parser.parse_args()
    process(
        args.input_sessions,
        args.input_output,
        args.input_calibrate_script,
        args.input_stack_script,
        args.input_process_dir,
        args.input_seq_name,
    )
