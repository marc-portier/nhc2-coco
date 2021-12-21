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
$ nhc2_coco discover
```

## Connect (test credentials) to your nhc2 host

The `connect` action allows to
* make a connection, and thus test out the authentication
* inspect the system-information provided by the nhc2 host

```bash
$ nhc2_coco connect
```

## List elements on your nhc2 host in a comprehensive reporting

todo

## Watch for events from elements on your nhc2 hosts

todo

## Open an interactive shell to interact with the elements on your nh2 host

todo
