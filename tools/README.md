# Prerequisites

- Python 3.10
- Make sure that pip can access the correct github repositories (visionapi and visionlib) by running `source set_local_git_creds.sh` and supplying your username and an access token, which has read access to vision-api and vision-lib. On some systems Git seems to be able to pick up ssh keys automatically...
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
You can exit the program by pressing `q`.

### Examples
- `python watch.py` displays a menu with all available streams for ease of use (and after selection renders content of that stream)
- `python watch.py -h` shows all available options
- `python watch.py -s objectdetector:video1` renders frames with detected objects (assuming that `objectdetector:*` contains outputs of the objectdetector stage, which is default)

### Caveats
- The annotations are not exactly pretty anymore, because I wanted to remove the dependency on the ultralytics library (which has great plotting features) -> you are more than welcome to improve that :)
- Data transfer from Redis and rendering will increase your system load by another few percent
