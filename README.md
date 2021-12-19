# pynhc2

License: MIT

## Usage as Python Code Library

### Create a NHC2 object

```python
NHC2(address, username, password, port, ca_path, switches_as_lights)
```

* __address__ - IP or host of the connected controller
* __username__ - The UUID of the profile
* __password__ - The password
* __port__ - (optional) The MQTT port. Default = 8883
* __ca_path__ - (optional) Path of the CA file. Default = included CA file.
* __switches_as_lights__ - (optional) socket and switched-generic show up as lights.

 example:

 ```python
 coco = NHC2('192.168.1.2', 'abcdefgh-ijkl-mnop-qrst-uvwxyz012345', 'secret_password')
 ```

### What is supported?
light, socket, switched-generic, dimmer

### What now?
 TODO - write doc.

 TODO - refactor into logical groups that match niko documentation (NHC Relay Action, NHC Dimmer Action, etc)


## Usage as Command Line tool

This package comes with a standalone command line tool you can use to inspect your nhc2 configuration.

Read the included `--help`, or the [documentation](docs/cli) to see what it can do.

``` bash
$ nhc2_coco --help       # if you have the py module properly installed this script should be in your path
$ ./nhc2_coco.sh --help  # if you are just working off a local git checkout, this wrapper will do the same
```

The behaviour of the tool is controlled by two additional files:

| filename             | is used to specify | see example at |
|----------------------|--------------------|----------------|
| `.env`               | environment variables you otherwise need to provide through cli --arguments | `dotenv-example` |
| `«your»-logconf.yml` | specific rules on how to handle, capture, filter, format logging output | `debug-logconf.yml` |


## What can you do to help?

 * Contribute to this project with constructive issues, suggestions, PRs, etc.
 * Help me in any way to get support for more entities (eg heating)

Contributors might want to check up on this [guide](CONTRIBUTE)
