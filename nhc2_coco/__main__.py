from dotenv import load_dotenv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
from collections import namedtuple
import os
import sys
import asyncio
import threading
import datetime
import json
import logging
import logging.config
from nhc2_coco.coco_discover_profiles import CoCoDiscoverProfiles
from nhc2_coco.coco_device_class import CoCoDeviceClass
from nhc2_coco.coco_login_validation import CoCoLoginValidation
from nhc2_coco.const import MQTT_RC_CODES
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


def assertConnectionSettings(creds):
    assert creds.host is not None, "This action requires a host to connect to."
    assert creds.port is not None and creds.port != 0, "This action requires a port to connect to."
    assert creds.user is not None, "This action requires a user to connect to the nhc2 host."
    assert creds.pswd is not None, "This action requires a password to connect to the nhc2 host."


async def do_connect(creds, args):
    assertConnectionSettings(creds)
    clout(f"Testing connection to host '{creds.host}'")

    response_texts = list(MQTT_RC_CODES)
    response_texts[0] = 'Connection successful'

    clv = CoCoLoginValidation(creds.host, creds.user, creds.pswd, creds.port)
    resp = await clv.check_connection()
    if resp < len(response_texts):
        clout(response_texts[resp], em=True)
    else:
        clout(f"Connection FAILED (with unkown response code == {resp})", em=True)


async def do_info(creds, args):
    assertConnectionSettings(creds)
    clout(f"Getting System-Info from host '{creds.host}'")

    coco = CoCo(creds.host, creds.user, creds.pswd, creds.port)

    # on succes sys info will be available - so handle that
    def sysinfo_handler(info):
        clout("Sysinfo retrieved (connection succesful)", em=True)
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


class DeviceClassMonitor:
    """ A helper class to deal with all devices (per type) known to a nhc2 hosts
    """

    def __init__(self, types: list, found_devices_cb, on_all_registered):
        """ Initialize a monitor for the listed type_names, calling back to on_all_registered when last was received.
        """
        self._known_types = types
        self._remaining_types = None
        self._found_devices_cb = found_devices_cb
        self._on_all_registered = on_all_registered
        self._reset_types()

    def _reset_types(self):
        self._remaining_types = list(self._known_types)

    def _handling_complete(self, cdc):
        """ Mark the handling of one CoCoDeviceClass
        """
        # remove name from type_names
        self._remaining_types.remove(cdc.value)
        # disconnect if none left
        if len(self._remaining_types) == 0:
            _LOGGER.debug("done receiving all requested types.")
            try:
                self._on_all_registered()
            except Exception as e:
                _LOGGER.exception(e)

    def _handle_factory(self, cdc):
        """ Makes a handler for this type of devices
        """
        def handler(all):
            try:
                self._found_devices_cb(all, cdc)
            except Exception as e:
                _LOGGER.exception(e)
            finally:
                self._handling_complete(cdc)
        return handler

    def process_devices(self, coco):
        """ Start processing all known devivces of the initized typenames on the passed nhc2 host
        """
        coco.connect()
        self._reset_types()
        for name in self._remaining_types:
            _LOGGER.debug(f"DCM starting on {name}")
            cdc = CoCoDeviceClass(name)
            coco.get_devices(cdc, self._handle_factory(cdc))


async def do_list(creds, args):
    assertConnectionSettings(creds)
    type_names = get_selected_types(args)

    clout(f"Listing devices known to host '{creds.host}' of type: {type_names}")

    def all_done():
        coco.disconnect()

    def devices_found(all, cdc):
        clout(f"Found {len(all)} device(s) of type '{cdc.value}'", em=True)
        for dev in all:
            try:
                clout(f"  {dev}")
            except Exception as e:
                clout(f"  *** ERR *** report-failure: {e}")
                _LOGGER.exception(e)

    dcm = DeviceClassMonitor(type_names, devices_found, all_done)
    coco = CoCo(creds.host, creds.user, creds.pswd, creds.port)
    dcm.process_devices(coco)


def isotime():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def get_lapse(args: Namespace):
    lapse = int(args.time)
    assert lapse == -1 or lapse > 0, "Parameter for «time» seconds to wait should be either positive or -1 to disable timeout."
    lapse = None if lapse == -1 else lapse  # recode -1 to None so to use it in threading.Event.wait(lapse)
    return lapse


class EndWaitMonitor:
    """ Helper class to allow quit-command from stdin
    """
    def __init__(self, *quit_commands):
        self._quit_commands = [qc.upper() for qc in quit_commands]
        self._event = threading.Event()
        self._thread = threading.Thread(target=self._listen_for_quit_command, daemon=True)
        self._start()

    def _start(self):
        self._thread.start()

    def _end(self):
        self._event.set()

    def end(self):
        """ Forcefully make wait() return
        """
        self._end()

    def _listen_for_quit_command(self):
        listening = True
        while listening:
            answ = input().upper()
            for qc in self._quit_commands:
                if qc.startswith(answ):
                    listening = False
        _LOGGER.debug("keyboard quit received")
        self._end()

    def wait(self, timeout=None):
        """ Wait for received quit command, or bail out after timeout
        """
        return self._event.wait(timeout)


async def do_watch(creds, args):
    assertConnectionSettings(creds)
    type_names = get_selected_types(args)
    uuid = args.uuid
    lapse = get_lapse(args)
    monitoring = list()
    clout(f"Watching devices known to host '{creds.host}' of type: {type_names} or matching uuid: {uuid}")

    def is_matching(dev_uuid):
        """ if uuid is set, only that one matches, else all do
        """
        return uuid is None or dev_uuid.startswith(uuid)

    def all_done():
        if len(monitoring) == 0:
            clout("Nothing to monitor - exiting", em=True)
            ewm.end()
        else:
            clout(f"Actively monitoring {len(monitoring)} devices", em=True)

    def make_device_monitor(dev):
        def on_change():
            clout(f"@{isotime()}=>{dev}")
        return on_change

    def devices_found(all, cdc):
        _LOGGER.debug(f"getting {len(all)} devices of type {cdc.value}")
        for dev in all:
            if is_matching(dev.uuid):
                dev.on_change = make_device_monitor(dev)
                monitoring.append(dev)
                _LOGGER.debug(f"monitoring device: (type={cdc.value}, uuid={dev.uuid})")

    dcm = DeviceClassMonitor(type_names, devices_found, all_done)
    coco = CoCo(creds.host, creds.user, creds.pswd, creds.port)
    dcm.process_devices(coco)

    ewm = EndWaitMonitor("quit")  # allow for quit-command interrupt over stdin
    ewm.wait(lapse)  # wait for quit command or timeout - whatever happens first
    # clean up
    coco.disconnect()


STATE_ALIAS_MAP = {
    '1': 'on',
    '0': 'off',
    'x': 'toggle',
}


def get_newstate(args: Namespace):
    newstate = args.state[0].lower()
    newstate = STATE_ALIAS_MAP.get(newstate, newstate)  # replace value if in alias-map
    # refactoring::suggestion Device-States are probably best also coded as objects rather then just strings
    return newstate


async def do_act(creds, args: Namespace):
    assertConnectionSettings(creds)
    uuid = args.uuid[0]
    newstate = get_newstate(args)
    clout(f"Searching device '{uuid}' to set to {newstate}")

    found_devices = list()

    def is_matching(dev_uuid):
        """ if uuid is set, only that one matches, else all do
        """
        return uuid is None or dev_uuid.startswith(uuid)

    def end_action():
        coco.disconnect()

    def set_action(dev):
        def on_change():
            clout(f"state changed.\n{dev}")
            end_action()
        dev.on_change = on_change
        clout(f"setting device of class {type(dev).__name__} to {newstate}")
        dev.request_state_change(newstate)

    def all_done():
        if len(found_devices) == 0:
            clout("device not found - exiting", em=True)
            end_action()
        elif  len(found_devices) > 1:
            clout("ambiguous request, multiple devices found - narrow down to correct uuid please:", em=True)
            for dev in found_devices:
                clout(f" * {dev.uuid} -> {dev.name}")
            end_action()
        else:
            dev = found_devices[0]
            clout(f"Found device to act upon. Stand-by for effect. Current state:\n{dev}", em=True)
            set_action(dev)

    def devices_found(all, cdc):
        _LOGGER.debug(f"getting {len(all)} devices of type {cdc.value}")
        for dev in all:
            if is_matching(dev.uuid):
                found_devices.append(dev)
                _LOGGER.debug(f"found device: (type={cdc.value}, uuid={dev.uuid})")

    dcm = DeviceClassMonitor(DEVICE_TYPENAMES, devices_found, all_done)
    coco = CoCo(creds.host, creds.user, creds.pswd, creds.port)
    dcm.process_devices(coco)

    _LOGGER.info(f"TODO -- implement setting device {args.uuid} to {args.state}")


async def do_shell(creds, args: Namespace):
    _LOGGER.info("TODO -- implement an interactive shell to capture commands and 'talk' to the controller")
    # need to consider some command syntax ? construct a language and use some parser-generator ? (e.g. https://www.dabeaz.com/ply/)
    # might be useful in a separate branch?
    # + think well about how such shell language should look like


def action_alias_subs(word, *extra):
    """ Produce all leading substrings of the passed word to use as action aliases. Adds indvidual extra's too.
    """
    return [word[:n] for n in range(1, len(word))] + list(extra)


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
        metavar="LOGCONF_FILE.yml",
        type=str,
        action='store',
        help='The config file for the Logging in yml format',
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
        aliases=action_alias_subs('discover'),
        help='Discover all nhc2 systems on the network',
    ).set_defaults(func=do_discover)

    saps.add_parser(
        'connect',
        aliases=action_alias_subs('connect'),
        help='Test the connection to the controller',
    ).set_defaults(func=do_connect)

    saps.add_parser(
        'info',
        aliases=action_alias_subs('info'),
        help='Dump system info about the controller',
    ).set_defaults(func=do_info)

    listap = saps.add_parser(
        'list',
        aliases=action_alias_subs('list', 'ls'),
        help='List all elements found on the controller'
    )
    listap.add_argument(
        '-t', '--device_type',
        metavar="TYPE",
        action="store",
        help='device type to list -- will list all if ommitted',
    )
    listap.set_defaults(func=do_list)

    watchap = saps.add_parser(
        'watch',
        aliases=action_alias_subs('watch'),
        help='Watch and report all events on the controller'
    )
    watchap.add_argument(
        'time',
        metavar="SECONDS",
        nargs='?',
        default=300,  # 5 minutes
        action="store",
        help='device type to watch -- will watch all if ommitted',
    )
    watchap.add_argument(
        '-t', '--device_type',
        metavar="TYPE",
        action="store",
        help='device type to watch -- will watch all if ommitted',
    )
    watchap.add_argument(
        '-u', '--uuid',
        metavar="UUID",
        action="store",
        help='single device uuid (matching prefix is enough) to watch',
    )
    watchap.set_defaults(func=do_watch)

    actap = saps.add_parser(
        'act',
        aliases=action_alias_subs('act'),
        help='Set a particular device to on/off/toggle'
    )
    actap.add_argument(
        'uuid',
        metavar="UUID",
        action="store",
        nargs=1,
        help='single device uuid (matching prefix is enough) to set',
    )
    actap.add_argument(
        'state',
        metavar="STATE",
        action="store",
        nargs=1,
        help='ON | 0 | OFF | 1 | TOGGLE | x | LOW | MEDIUM | HIGH | BOOST | «percentage»% | «degrees»C',
    )
    actap.set_defaults(func=do_act)

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
    # host == '@' is forcing to look around - use case override: .env setting with cli
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
