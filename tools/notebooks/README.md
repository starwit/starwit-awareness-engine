# Notebooks & Analysis Scripts
A collection of Jupyter notebooks and small scripts for detail analysis of pipeline data.

**Looking for the introspection tools?** `watch.py`, `record.py`, `play.py`, `echo.py` and `plot.py` have moved to their own repository: [sae-introspection](https://github.com/starwit/sae-introspection) (installable via `pipx install git+https://github.com/starwit/sae-introspection.git`, providing the commands `sae-watch`, `sae-record`, `sae-play`, `sae-echo` and `sae-plot`).

## Prerequisites
- Python >=3.10, Poetry >=2.0.0
- Install dependencies: `poetry install`
- Install libturbojpeg on your OS (e.g. `apt install libturbojpeg`)
- Run `poetry run python <script>` or `poetry run jupyter lab` for the notebooks

## Contents
- `geo-mapper-visualizer.ipynb` - Visualizes geo mapper input/output on a map to check the mapping configuration
- `plot-gps-log.ipynb` - Plots a recorded GPS log
- `waste.ipynb` - Scratchpad notebook
- `inspect_stream.py` - Attaches to a Redis stream and prints frame timestamps of the received `SaeMessage`s
- `stats.py` - Polls the Prometheus endpoint of a component and prints live counter/summary metrics (e.g. `python stats.py 8000`)
