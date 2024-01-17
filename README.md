# siril-multi-night
Process astrophotography data from multiple nights using Siril.

[Siril](https://siril.org) is a popular, open source astrophotography processing tool, but it lacks an automated approach to processing data across multiple nights. `siril-multi-night` provides a simple CLI and python module that aims to fill this gap.

## Usage

### Prerequisite

- [siril-cli](https://siril.org/download/) (comes with the Siril desktop application)

### CLI

Install dependencies to a [venv](https://docs.python.org/3/library/venv.html)
```sh
# create the venv
python -m venv .venv
# activate the venv
source .venv/bin/activate
# install dependencies
python -m pip install -r requirements.txt
```

Run `siril-multi-night`
```sh
python3 siril_multi_night.py \
	--sessions path/to/session1 path/to/session2 \
	--calibrate-script path/to/calibrate-script.ssf \
	--stack-script path/to/stack-script.ssf \
	-o ./output
```

#### Options

| Option | Required | Default | Description |
| - | - | - | - |
| `--sessions` | ✅ | | The list of paths to the sessions of data. |
| `--calibrate-script` | ✅ | | The path to the Siril calibration script. |
| `--stack-script` | ✅ | | The path to the Siril stacking file. |
| `-o, --output` | ✅ | | The path to the output directory. |
| `-p, --process-dir` | ❌ | `process` | The name of the Siril process directories. |
| `--seq-name` | ❌ | `pp_light` | The sequence name of the preprocessed light files. |
