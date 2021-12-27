# Command Line Interface

This document tries to capture and explain what you can do with the provided CLI tool

## Read the cli help

run `nhc2_coco --help` to retrieve:
```
usage: nhc2_coco [-h] [-l <path to logconf file in yml format>] [-H HOST] [-p PORT] [-U USERNAME] [-P PASSWORD] action ...

CLI for nhc2_coco

optional arguments:
  -h, --help            show this help message and exit
  -l <path to logconf file in yml format>, --logconf <path to logconf file in yml format>
                        where to move the logging to (default: None)
  -H HOST, --host HOST  Specify host (name or ip) Niko-Home-Controller (default: None)
  -p PORT, --port PORT  Specify portnumber (default: None)
  -U USERNAME, --user USERNAME
                        User to authenticate (default: None)
  -P PASSWORD, --pswd PASSWORD
                        password to authenticate (default: None)

actions to perform:
  action
    discover (d, disc)  Discover all nhc2 systems on the network
    connect (c, con)    Test the connection to the controller
    list (l, ls)        List all elements found on the controller
    watch (w, wat)      Watch and report all events on the controller
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
$ nhc2_coco list            # list all devices
$ nhc2_coco ls -t lights    # list only the lights
```

## Watch for events from elements on your nhc2 hosts

The `watch` action allows to
* listen to on_change events of specific devices (selectable by -t «type» or even -u «uuid»)
* on each event a basic device-state will be added to stdout

```bash
$ nhc2_coco watch                  # watch all devices and keep doing that
$ nhc2_coco watch 30  -t lights    # only watch devices of type 'lights' and stop after 30s
$ nhc2_coco watch 300 -u 2ae61bad  # only watch devices with matching uuid and stop after 5' (=300")
```

## Trigger an actual action on your nhc2 host

todo


## Open an interactive shell to interact with the elements on your nh2 host

todo
