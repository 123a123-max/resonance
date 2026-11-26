import argparse
from contextlib import ExitStack
import ipaddress
import os
import socket
from threading import Thread
import webbrowser

import uvicorn


class LocalServer(uvicorn.Server):
    async def startup(self, sockets=None):
        await super().startup(sockets=sockets)
        if not self.started:
            return
        desktop_url = f'http://localhost:{self.config.port}/'
        print(f'Desktop: {desktop_url}', flush=True)
        if self.lan_origin:
            print(f'Phone on the same network: {self.lan_origin}/', flush=True)
        else:
            print('No LAN address found. Only this computer can open the preview.', flush=True)
        if self.open_browser:
            Thread(target=webbrowser.open, args=(desktop_url,), daemon=True).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--lan', type=ipaddress.IPv4Address)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()

    with ExitStack() as stack:
        try:
            sockets = [stack.enter_context(socket.create_server(('127.0.0.1', args.port)))]
        except OSError as error:
            parser.exit(1, f'Cannot listen on desktop port {args.port}: {error}\n')

        lan_origin = None
        if args.lan and not (args.lan.is_loopback or args.lan.is_unspecified):
            try:
                sockets.append(stack.enter_context(socket.create_server((str(args.lan), args.port))))
                lan_origin = f'http://{args.lan}:{args.port}'
            except OSError as error:
                print(f'Cannot listen on LAN address {args.lan}: {error}', flush=True)
        if lan_origin:
            os.environ['PLOG_INVITE_ORIGIN'] = lan_origin
        else:
            os.environ.pop('PLOG_INVITE_ORIGIN', None)

        server = LocalServer(uvicorn.Config('main:app', host='127.0.0.1', port=args.port))
        server.lan_origin = lan_origin
        server.open_browser = not args.no_browser
        server.run(sockets=sockets)


if __name__ == '__main__':
    main()
