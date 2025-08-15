# Prerequisites

- Python >=3.12, Poetry >=2.0.0
- Install dependencies: `poetry install`
- Install libturbojpeg on your OS (e.g. `apt install libturbojpeg`)
- Run `poetry run python <script>`

# Tools
These tools were originally made for `SaeMessages`, however, the `echo.py` script supports more vision-api message types (see below).

## Visual Introspection (`watch.py`)
The `watch.py` script can be used to visually look into the data flows within the pipeline.
On a technical level, it attaches to a Redis stream of your choice and then tries to guess from the name prefix which stage output it has to decode. 
It will then render (and annotate, if possible) every output object / proto it receives from Redis.
You can exit the program by pressing `q` in the video window or hitting Ctrl-C on the CLI.

### Create video from output
Find out the frame size and framerate, then run (replacing `-r 10` (fps) and `-s 3840x2160` (size in px) with the appropriate values):\
`python watch.py -o | ffmpeg -y -pix_fmt bgr24 -f rawvideo -r 10 -s 3840x2160 -i - -c:v libx264 -crf 25 out.mp4`\
You can increase the quality (and file size) by lowering the `crf` value (-6 approx. doubles the file size)

### Examples
- `python watch.py` displays a menu with all available streams for ease of use (and after selection renders content of that stream)
- `python watch.py --help` shows all available options
- `python watch.py -s objectdetector:video1` renders frames with detected objects (assuming that `objectdetector:*` contains outputs of the objectdetector stage, which is default)

### Caveats
- Data transfer from Redis and rendering will increase your system load by another few percent


## Pipeline Recording (`record.py`)
The `record.py` script provides a simple way to record messages from some or all Redis streams into a file, i.e. create a log of all pipeline activities / state.
See `python record.py --help` for how to use it. \
For creating longer recordings, the script offers several options to control the file size, as JPEG frames are very big in comparison to efficient video codecs like H.264/H.265 and there are some inefficiencies regarding space in the saedump format. `-r` / `--remove-frame` removes frames from messages before writing them to the dump file. `-d` / `--downscale-frames` (with `-q` / `--downscale-jpeg-quality`) enables trading some quality loss for smaller file sizes.

### Examples
- `python record.py -s geomapper:StreamID -t 86400 -d 320 -q 90 -o output.saedump` records 24 hours of geomapper output, scaling down video frames to a width of 320px (at a quality of 90%)


## Pipeline Playback (`play.py`)
The `play.py` script plays back a pipeline log into a running pipeline (i.e. at least a running Redis instance). It'll read the log file it is given and play back all messages into the corresponding streams they were recorded from. The messages will be spaced exactly as they were recorded (i.e. a 5fps recording will be played back at the same speed). For many real-world test cases the option `-t` might be interesting, which enables rewriting the message timestamps to the present moment (while still preserving message cadence).
See `python play.py --help` for how to use it.


## JSON Output (`echo.py`)
The `echo.py` script echoes all messages it receives into stdout as a JSON string (output of protobufs `MessageToJSON()`), everything else goes to stderr. It currently supports `SaeMessage`, `DetectionCountMessage` and `PositionMessage` - the message type on the chosen stream is autodetected (either using the type field or if that is not set a rather crude heuristic is used). All selected streams must carry the same message type. For `SaeMessage` payloads frame data is removed by default as to not clutter the output.\
`echo.py` can be very useful when combined with other tools like jq. For example, to print the source id, frame timestamp and number of detections for each received message: `python echo.py | jq -r '[.frame.sourceId, .frame.timestampUtcMs, (.detections | length)] | @tsv'`