# -*- coding: utf-8 -*-

import sys
import shlex
import subprocess
import socket


def check_connection(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.shutdown(1)
    except socket.gaierror:
        return False
    except ConnectionRefusedError:
        return False
    else:
        return True


def setup_signal(handler=None):
    import signal
    SIGNALS = {
        signal.SIGHUP: 'SIGHUP',
        signal.SIGINT: 'SIGINT',
        signal.SIGTERM: 'SIGTERM',
    }

    def exit_handler(signum, frame):
        # import traceback
        # stack = traceback.format_stack(frame)
        # print(f'\n{"".join(stack)}\n')
        import colorama
        print(f'{colorama.Fore.WHITE}[ SIGNAL ] : {signum} - {SIGNALS[signum]}{colorama.Fore.RESET}')
        sys.exit(0)

    def wrapped_handler(signum, frame):
        # new line after ^C
        print()

        if handler:
            handler(signum, frame)
        else:
            exit_handler(signum, frame)

    # catch kill signal except for SIGKILL(9) / SIGSTOP(19)
    for signum in SIGNALS:
        signal.signal(signum, wrapped_handler)


def rsync_files(src='', dst='', pem='', options='-azq'):
    tunnel = f"ssh -o 'StrictHostKeyChecking no' -i {pem}"
    cmd = f'rsync -e "{tunnel}" {options} {src} {dst}'
    process = subprocess.Popen(
        shlex.split(cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    if stderr:
        raise Exception(stderr.decode('utf8'))
