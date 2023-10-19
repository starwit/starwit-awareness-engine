# Tools

## Visual Introspection
The `watch.py` script can be used to visually look into the data flows within the pipeline.
On a technical level, it attaches to a Redis stream of your choice and then tries to guess from the name prefix which stage output it has to decode. 
It will then render (and annotate, if possible) every output object / proto it receives from Redis.
You can exit the program by pressing `q`.
Example:
- `python demo.py -s objectdetector:video1` renders frames with detected objects (assuming that `objectdetector:*` contains outputs of the objectdetector stage, which is default)

### Caveats
- The annotations are not exactly pretty anymore, because I wanted to remove the dependency on the ultralytics library (which has great plotting features) -> you are more than welcome to improve that :)
- Data transfer from Redis and rendering will increase your system load by another few percent
