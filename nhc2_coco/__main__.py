from dotenv import load_dotenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from collections import namedtuple
import os
import sys
import asyncio
import json
import logging
import logging.config
from nhc2_coco.coco_discover_profiles import CoCoDiscoverProfiles
from nhc2_coco.coco_device_class import CoCoDeviceClass
from nhc2_coco.coco_login_validation import CoCoLoginValidation
from nhc2_coco import CoCo


_LOGGER = logging.getLogger(__name__)
DEFAULT_HOST = 'nhc2.local'
DEFAULT_PORT = 8883
DEVICE_TYPES = set(CoCoDeviceClass)  # list of all items in the enum
DEVICE_TYPENAMES = {cdc.value for cdc in DEVICE_TYPES}


def clout(*msg, em=False):
    """Output actually intended as command-line response output. All other statements should use _LOGGER
    :param *msg: message to output
    :type *msg: str or tuple thereof
    :param em: add emphasis (underline) to the message
    :type em: bool
    """
    msg = ' '.join(map(lambda m: str(m), msg))
    if em:
        msg = '\033[4m' + msg + '\033[0m'  # add emphasis by underlining the text
    print(msg)


async def do_discover(creds, args: Namespace):
    """Performs NHC2_COCO Discovery
    :param creds: Namedtuple holding the host:port and user:pass credentials
    :param args: the parsed cli arguments
    """
    if creds.host is None:
        clout('Searching for NiKo Home Control Controllers and profiles on them...')
    else:
        clout('Listing Profiles on host [%s] use `--host @` to ignore the .env host and perform broadcast-discovery.' % creds.host)

    disc = CoCoDiscoverProfiles(creds.host)
    results = await disc.get_all_profiles()

    clout('Discovery completed. Listing discovered Profiles for %d controller(s).\n' % (len(results)))

    for i, result in enumerate(results):
        clout('Controller #%d' % i, em=True)
        ip, mac, profiles, host = tuple(result[k] for k in range(4))
        clout(f' IP:   {ip}\n Host: {host}\n MAC:  {mac}')
        clout(' %d profile(s) found.' % (len(profiles)))
        for j, profile in enumerate(profiles):
            clout(' Profile #%d:' % j)
            uuid, name, type = tuple(profile.get(k) for k in ('Uuid', 'Name', 'Type'))
            clout(f'  uuid: {uuid}\n  Name: {name}\n  Type: {type}')


def assertConnectionSettings (creds):
    assert creds.host is not None, "This action requires a host to connect to."
    assert creds.port is not None and creds.port != 0 , "This action requires a port to connect to."
    assert creds.user is not None, "This action requires a user to connect to the nhc2 host."
    assert creds.pswd is not None, "This action requires a password to connect to the nhc2 host."

async def do_connect(creds, args):
    assertConnectionSettings(creds)
    clout(f"Testing connection to host '{creds.host}'")

    clv = CoCoLoginValidation(creds.host, creds.user, creds.pswd, creds.port)
    resp = await clv.check_connection()
    if resp == 0:
        clout(f"Connection SUCCESFUL", em=True)
    else:
        clout(f"Connection FAILED (response == {resp})", em=True)


async def do_info(creds, args):
    assertConnectionSettings(creds)
    clout(f"Getting System-Info from host '{creds.host}'")

    coco = CoCo(creds.host, creds.user, creds.pswd, creds.port)

    # on succes sys info will be available - so handle that
    def sysinfo_handler(info):
        clout(f"Sysinfo retrieved (connection succesful)", em=True)
        clout(json.dumps(info, indent=4))
        coco.disconnect()
    # on error - we assume the connection failed
    def error_handler(error):
        (reason, code, mqtt_msg) = error
        clout(f"***ERROR***: {reason} - [{code}] = {mqtt_msg}")
        coco.disconnect()  # close the coco-thread

    # register event-handlers
    coco.get_systeminfo(sysinfo_handler)
    coco.on_error(error_handler)

    # try and connect
    coco.connect()

def get_selected_types(args):
    type_names = DEVICE_TYPENAMES
    type_name = args.device_type
    if type_name is not None:
        type_name = type_name.lower()
        assert type_name in DEVICE_TYPENAMES, f"requested type {type_name} must be one of {DEVICE_TYPENAMES}"
        type_names = {type_name}
    return type_names

async def do_list(creds, args):
    assertConnectionSettings(creds)
    type_names = get_selected_types(args)

    clout(f"Listing devices known to host '{creds.host}' of type: {type_names}")

    def done_device_class(cdc):
        # remove name from type_names
        type_names.remove(cdc.value)
        # disconnect if none left
        if len(type_names) == 0:
            coco.disconnect()
    def make_class_handler(cdc):
        tname = cdc.value
        def handler(all):
            clout(f"Found {len(all)} device(s) of type '{tname}'", em=True)
            for dev in all:
                try:
                    clout(f"  {dev}")
                except Exception as e:
                    clout(f"  *** ERR *** report-failure: {e}")
                    _LOGGER.exception(e)
            done_device_class(cdc)
        return handler

    coco = CoCo(creds.host, creds.user, creds.pswd, creds.port)
    coco.connect()
    for name in type_names:
        cdc = CoCoDeviceClass(name)
        coco.get_devices(cdc, make_class_handler(cdc))


async def do_watch(creds, args):
    _LOGGER.info("TODO -- implement watch mode reporting on all events")
    # todo allow specify TYPE of elements to list
    # listen for input keys --> disconnect on any key


async def do_shell(creds, args):
    _LOGGER.info("TODO -- implement an interactive shell to capture commands and 'talk' to the controller")
    # need to consider some command syntax ? construct a language and use some parser-generator ?
    # might be useful in a separate project?


def get_arg_parser():
    """ Defines the arguments to this module's __main__ cli script
    by using Python's [argparse](https://docs.python.org/3/library/argparse.html)
    """
    ap = ArgumentParser(
        prog='nhc2_coco',
        description='CLI for nhc2_coco',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        '-l', '--logconf',
        metavar="<path to logconf file in yml format>",
        type=str,
        action='store',
        help='where to move the logging to',
    )
    ap.add_argument(
        '-H', '--host',
        metavar="HOST",
        action="store",
        help='Specify host (name or ip) Niko-Home-Controller',
    )
    ap.add_argument(
        '-p', '--port',
        metavar="PORT",
        action="store",
        help='Specify portnumber',
    )
    ap.add_argument(
        '-U', '--user',
        metavar="USERNAME",
        action="store",
        help='User to authenticate',
    )
    ap.add_argument(
        '-P', '--pswd',
        metavar="PASSWORD",
        action="store",
        help='password to authenticate',
    )

    saps = ap.add_subparsers(
        title='actions to perform',
        required=True,
        metavar="action",
    )

    saps.add_parser(
        'discover',
        aliases=['d', 'disc'],
        help='Discover all nhc2 systems on the network',
    ).set_defaults(func=do_discover)

    saps.add_parser(
        'connect',
        aliases=['c', 'con', 'conn'],
        help='Test the connection to the controller',
    ).set_defaults(func=do_connect)

    saps.add_parser(
        'info',
        aliases=['i', 'info'],
        help='Dump system info about the controller',
    ).set_defaults(func=do_info)

    listap = saps.add_parser(
        'list',
        aliases=['l', 'ls'],
        help='List all elements found on the controller'
    )
    listap.add_argument(
        '-t', '--device_type',
        metavar="TYPE",
        action="store",
        help='device type to list -- will list all if ommitted',
    )
    listap.set_defaults(func=do_list)

    saps.add_parser(
        'watch',
        aliases=['w', 'wat'],
        help='Watch and report all events on the controller'
    ).set_defaults(func=do_watch)

    saps.add_parser(
        'shell',
        aliases=['s', 'sh'],
        help='Open an interactive shell to communicate to the controller'
    ).set_defaults(func=do_shell)

    return ap


def credentials(args: Namespace):
    """Returns a simple structure holding the to be applied credentials merged from CLI args and .env
    """
    host = args.host if args.host else os.environ.get('NHC2_HOST', DEFAULT_HOST)
    # host == '@' is forcing to look around - use case override:  .env on cli
    host = None if host == '@' else host
    port = int(args.port if args.port else os.environ.get('NHC2_PORT', DEFAULT_PORT))
    user = args.user if args.user else os.environ.get('NHC2_USER')
    pswd = args.pswd if args.pswd else os.environ.get('NHC2_PASS')
    pwsc = pswd[:3] + ".." + pswd[-2:]
    return namedtuple("Credentials", ["host", "port", "user", "pswd", "pwsc"])(host, port, user, pswd, pwsc)


def enable_logging(args: Namespace):
    """Configures logging based on logconf specified through -l argument or .env ${NHC2_LOGCONF}
    """
    logconf = args.logconf if args.logconf else os.environ.get('NHC2_LOGCONF')
    if logconf is None or logconf == '':
        return
    # else
    import yaml   # conditional dependency -- we only need this (for now) when logconf needs to be read
    with open(logconf, 'r') as yml_logconf:
        logging.config.dictConfig(yaml.load(yml_logconf, Loader=yaml.SafeLoader))
    _LOGGER.info(f"Logging enabled according to config in {logconf}")


def main():
    """ CLI entry function
    """
    exitcode = 0
    load_dotenv()              # allow passing credentials and logging settings through dot-env strategy
    ap = get_arg_parser()
    args = ap.parse_args()     # interprete cli args
    enable_logging(args)       # merge args and .env to enable logging
    creds = credentials(args)  # merge args and .env to get credentials
    _LOGGER.info(f"credentials => host={creds.host}, port={creds.port}, user={creds.user}, pswd={creds.pwsc}")

    # setup async wait construct for main routines
    loop = asyncio.get_event_loop()
    try:
        # trigger the actual called action-function (async) and wait for it
        loop.run_until_complete(args.func(creds, args))
    except Exception as e:
        _LOGGER.exception(e)
        clout("***Error***", str(e))
        ap.print_help()
        exitcode = 1
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        sys.exit(exitcode)


if __name__ == "__main__":
    main()
