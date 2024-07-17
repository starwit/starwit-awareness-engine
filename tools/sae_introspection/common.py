import argparse
import signal
import threading

from simple_term_menu import TerminalMenu


def choose_stream(redis_client):
    available_streams = sorted(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM', count=100)[1]))
    menu = TerminalMenu(available_streams, title='Choose Redis stream to attach to:', show_search_hint=True)
    selected_idx = menu.show()
    if selected_idx is None:
        print('No stream chosen. Exiting.')
        exit(0)
    return available_streams[selected_idx]

def choose_streams(redis_client):
    available_streams = sorted(map(lambda b: b.decode('utf-8'), redis_client.scan(_type='STREAM', count=100)[1]))
    menu = TerminalMenu(
        available_streams, 
        title='Choose Redis streams to attach to:', 
        show_search_hint=True,
        multi_select=True,
        multi_select_empty_ok=True,
        multi_select_select_on_accept=False,
        show_multi_select_hint=True,
    )
    selected_idx_list = menu.show()
    if selected_idx_list is None:
        print('No stream chosen. Exiting.')
        exit(0)
    return [available_streams[idx] for idx in selected_idx_list]

def default_arg_parser():
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument('--help', action='help', help='Show help message and exit')
    arg_parser.add_argument('-h', '--redis-host', type=str, default='localhost')
    arg_parser.add_argument('-p', '--redis-port', type=int, default=6379)
    return arg_parser

def register_stop_handler():
    stop_event = threading.Event()

    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    return stop_event