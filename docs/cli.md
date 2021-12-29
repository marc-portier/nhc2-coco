# Command Line Interface

This document tries to capture and explain what you can do with the provided CLI tool

## Read the cli help

run `nhc2_coco --help` to retrieve:
```
usage: nhc2_coco [-h] [-l LOGCONF_FILE.yml] [-H HOST] [-p PORT] [-U USERNAME] [-P PASSWORD] action ...

CLI for nhc2_coco

optional arguments:
  -h, --help            show this help message and exit
  -l LOGCONF_FILE.yml, --logconf LOGCONF_FILE.yml
                        The config file for the Logging in yml format (default: None)
  -H HOST, --host HOST  Specify host (name or ip) Niko-Home-Controller (default: None)
  -p PORT, --port PORT  Specify portnumber (default: None)
  -U USERNAME, --user USERNAME
                        User to authenticate (default: None)
  -P PASSWORD, --pswd PASSWORD
                        password to authenticate (default: None)

actions to perform:
  action
    discover (d, di, dis, disc, disco, discov, discove)
                        Discover all nhc2 systems on the network
    connect (c, co, con, conn, conne, connec)
                        Test the connection to the controller
    info (i, in, inf)   Dump system info about the controller
    list (l, li, lis, ls)
                        List all elements found on the controller
    watch (w, wa, wat, watc)
                        Watch and report all events on the controller
    act (a, ac)         Set a particular device to on/off/toggle
    shell (s, sh)       Open an interactive shell to communicate to the controller

```

## Discover nhc2 hosts and profiles on your network

The `discover` action allows to
* find Niko Home Controller hosts on your network using broadcasts
* list profiles found on top of them

```bash
$ nhc2_coco discover       # discover nhc2 hosts on any reachable broadcast network
```

## Connect (test credentials) to your nhc2 host

The `connect` action allows to
* make a connection, and thus validate your connection credentials

```bash
$ nhc2_coco connect         # test the connection
```

## Info about your nhc2 host

The `info` action allows to
* inspect the system-information provided by the nhc2 host

```bash
$ nhc2_coco info            # give system info
```

## List elements on your nhc2 host in a comprehensive reporting

The `list` action allows to
* list all the found devices on the nhc2 host, or limit the list to a specif type of device (lights, switches, ...)
* together with some basic state information on each of them

```bash
$ nhc2_coco list              # list all devices
$ nhc2_coco ls -t lights      # list only the lights
$ nhc2_coco l -n 'bath room'  # list only devices with names containing both 'bath' and 'room'
```

## Watch for events from elements on your nhc2 hosts

The `watch` action allows to
* listen to on_change events of specific devices (selectable by -t «type» or even -u «uuid»)
* on each event a basic device-state will be added to stdout

```bash
$ nhc2_coco watch                  # watch all devices and keep doing that
$ nhc2_coco watch 30  -t lights    # only watch devices of type 'lights' and stop after 30s
$ nhc2_coco watch 300 -u 2ae61bad  # only watch devices with matching uuid and stop after 5' (=300")
$ nhc2_coco watch 3 -n 'spots'     # only watch devices with matching name and stop after 3"
```

## Trigger an actual action on your nhc2 host

The `act` action allows to
* actually change the state of one of the devices on your nhc2 host
* in the process it will show the state of the device before and after

```bash
$ nhc2_coco act -u 98334ef ON             # sets the state of device with uuid matching (the lead characters of) the device uuid to ON
$ nhc2_coco act -n 'bathroom light' ON    # sets the state of device with matching name to ON
```

Depending on the type of object other values are supported:

| value             | effect                           | limited to types  |
|------------------:|----------------------------------|-------------------|
| on, off           | obvious                          | devices with on/off state
| toggle            | change on to off and vice versa  | (idem)
| 25%               | set as percentage of brightness  | dimmable lights
| low, medium, high, boost | set speed level of fan           | fans with controllable speed
| 21C               | desired temperature in degrees C | thermostat

## Open an interactive shell to interact with the elements on your nhc2 host

:warning: Unimplemented. For now, nothing more then a distant wish.  
Depends on some bright idea of what this should actually look like.
As well as on a clear and pressing need over the current cli features.

Maybe something like:
```bash
$ nhc2_coco sh
nhc2(-)> showenv         # show environment from memory: host, port, user, passwd (masked)
nhc2(-)> user «username» # set username to shell env in
nhc2(-)> pswd «passwd»   # similar
nhc2(-)> host «host»     # similar
nhc2(-)> port «port»     # similar
nhc2(-)> discover        # list available nhc2 hosts found on the connected networks

nhc2(-)> connect         # make Connection (using settings in env)

nhc2(host)>  ..          # more to come
```
