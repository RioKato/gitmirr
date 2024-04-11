from typing import Any


def clone(root: str, urls: list[str]):
    from subprocess import run
    from os import makedirs

    makedirs(root, exist_ok=True)

    for url in urls:
        run(['git', '-C', root, 'clone', '--mirror', url, urlhash(url)], check=True)


def update(root: str, urls: list[str]):
    from subprocess import run
    from os.path import join

    for url in urls:
        run(['git', '-C', join(root, urlhash(url)), 'remote', 'update'], check=True)


def cron(interval: int | str, path: str):
    from subprocess import run
    from sys import executable, argv
    from os.path import abspath
    from shlex import quote

    proc = run(['crontab', '-l'], capture_output=True, text=True)
    schedule = proc.stdout if not proc.returncode else ''

    if schedule and schedule[-1] != '\n':
        schedule += '\n'

    schedule += f'*/{interval} * * * * {quote(executable)} {quote(abspath(argv[0]))} update {quote(abspath(path))}\n'
    run(['crontab', '-'], check=True, input=schedule, text=True)


def daemon(root: str):
    from subprocess import run

    run(['git', 'daemon', '--export-all', f'--base-path={root}'], check=True)


def redirect(host: str, urls: list[str]):
    from subprocess import run

    while host.endswith('/'):
        host = host[:-1]

    for url in urls:
        run(['git', 'config', '--global', f'url.{host}/{urlhash(url)}.insteadOf', url],
            check=True)


def show(host: str, urls: list[str]):
    while host.endswith('/'):
        host = host[:-1]

    for url in urls:
        print(f'{url} => {host}/{urlhash(url)}')


def sample(path: str):
    from json import dump

    config = {
        'urls': [
            'https://github.com/torvalds/linux.git',
            'https://chromium.googlesource.com/v8/v8.git'
        ],
        'root': '/var/gitmirr',
        'host': 'git://localhost',
        'interval': 30
    }

    with open(path, 'w') as fd:
        dump(config, fd, indent=2)


def urlhash(url: str) -> str:
    from hashlib import sha256

    hash = sha256(url.encode()).hexdigest()
    return f'{hash}.git'


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    subparser_clone = subparsers.add_parser('clone')
    subparser_clone.add_argument('config')

    subparser_update = subparsers.add_parser('update')
    subparser_update.add_argument('config')

    subparser_cron = subparsers.add_parser('cron')
    subparser_cron.add_argument('config')

    subparser_daemon = subparsers.add_parser('daemon')
    subparser_daemon.add_argument('config')

    subparser_redirect = subparsers.add_parser('redirect')
    subparser_redirect.add_argument('config')

    subparser_show = subparsers.add_parser('show')
    subparser_show.add_argument('config')

    subparser_sample = subparsers.add_parser('sample')
    subparser_sample.add_argument('path')

    args = parser.parse_args()

    def loadconfg(path: str) -> Any:
        from json import load
        from types import SimpleNamespace

        with open(path) as fd:
            return load(fd, object_hook=lambda d: SimpleNamespace(**d))

    match args.command:
        case 'clone':
            config = loadconfg(args.config)
            clone(config.root, config.urls)

        case 'update':
            config = loadconfg(args.config)
            update(config.root, config.urls)

        case 'cron':
            config = loadconfg(args.config)
            cron(config.interval, args.config)

        case 'daemon':
            config = loadconfg(args.config)
            daemon(config.root)

        case 'redirect':
            config = loadconfg(args.config)
            redirect(config.host, config.urls)

        case 'show':
            config = loadconfg(args.config)
            show(config.host, config.urls)

        case 'sample':
            sample(args.path)

        case _:
            parser.print_help()
            exit(1)

    exit(0)


if __name__ == '__main__':
    main()
