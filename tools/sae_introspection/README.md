# Prerequisites

- Python >=3.10
- Create and activate python virtualenv
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```
- Install dependencies: `pip install -r requirements.txt`
- Install libturbojpeg on your OS (e.g. `apt install libturbojpeg`)

# Tools

## Visual Introspection (`watch.py`)
The `watch.py` script can be used to visually look into the data flows within the pipeline.
On a technical level, it attaches to a Redis stream of your choice and then tries to guess from the name prefix which stage output it has to decode. 
It will then render (and annotate, if possible) every output object / proto it receives from Redis.
You can exit the program by pressing `q` in the video window or hitting Ctrl-C on the CLI.

### Examples
- `python watch.py` displays a menu with all available streams for ease of use (and after selection renders content of that stream)
- `python watch.py --help` shows all available options
- `python watch.py -s objectdetector:video1` renders frames with detected objects (assuming that `objectdetector:*` contains outputs of the objectdetector stage, which is default)

### Caveats
- The annotations are not exactly pretty anymore, because I wanted to remove the dependency on the ultralytics library (which has great plotting features) -> you are more than welcome to improve that :)
- Data transfer from Redis and rendering will increase your system load by another few percent

## Pipeline Recording (`record.py`)
The `record.py` script provides a simple way to record messages from some or all Redis streams into a file, i.e. create a log of all pipeline activities / state.
See `python record.py --help` for how to use it.

## Pipeline Playback (`play.py`)
The `play.py` script plays back a pipeline log into a running pipeline (i.e. at least a running Redis instance). It'll read the log file it is given and play back all messages into the corresponding streams they were recorded from. The messages will be spaced exactly as they were recorded (i.e. a 5fps recording will be played back at the same speed). For many real-world test cases the option `-t` might be interesting, which enables rewriting the message timestamps to the present moment (while still preserving message cadence).
See `python play.py --help` for how to use it.

## JSON Output (`echo.py`)
The `echo.py` script echoes all SAE messages it receives into stdout as a JSON string (output of protobufs `MessageToJSON()`). Frame data is removed by default as to not clutter the output. `echo.py` can be very useful when combined with other tools like jq. For example, to print the source id, frame timestamp and number of detections for each received message: `python echo.py | jq -r '[.frame.sourceId, .frame.timestampUtcMs, (.detections | length)] | @tsv'`