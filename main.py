import argparse
import configparser
import sys
import logging
import os

from bitbucket.client import Client
from git import Repo
from git import RemoteProgress
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text
from bitbucket.exceptions import NotAuthenticatedError, NotFoundError, DestinationPathError

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class MyProgressPrinter(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")


def clone_repo(url: str, destination: str):
    logging.info('Cloning {} into {}'.format(url, destination))
    cloned_repo = Repo.clone_from(url, destination)


def update_repo(url: str, destination: str):
    logging.info('Updating {} into {}'.format(url, destination))
    repo = Repo(destination)
    assert not repo.bare
    assert not repo.is_dirty()
    origin = repo.remote()
    assert origin.exists()
    for fetch_info in origin.pull(progress=MyProgressPrinter()):
        print("Updated %s to %s" % (fetch_info.ref, fetch_info.commit))


def clone_repo_list(repo_list: list, clone_protocol: str, destination_path: str) -> dict:
    stats = {'updated' : 0, 'updated_fail': 0, 'cloned': 0, 'cloned_fail': 0}
    for repo in repo_list:
        dest_path = os.path.join(destination_path, repo.get('project').get('name'), repo.get('name'))
        repo_address = repo.get('links').get('clone')[0].get('href') if clone_protocol == 'https' else repo.get('links').get('clone')[1].get('href')
        if os.path.isdir(dest_path):
            try:
                update_repo(repo_address, dest_path)
                stats['updated'] = stats['updated'] + 1
            except:
                logging.warning('Repo {} had some problems during cloning'.format(repo.get('name')))
                stats['updated_fail'] = stats['fail'] + 1
                pass
        else:
            try:
                clone_repo(repo_address, dest_path)
                stats['cloned'] = stats['cloned'] + 1
            except:
                logging.warning('Repo {} had some problems during cloning'.format(repo.get('name')))
                stats['cloned_fail'] = stats['cloned_fail'] + 1
                pass
    return stats


def get_all_repos(client: Client, workspace: str = None) -> list:
    logging.info('Getting repositories information for workspace {}.'.format(workspace))
    response = client.get_repositories(next_url=None, workspace=workspace, params={'pagelen': 50})
    repos = response.get('values')
    next_page = response.get('next')
    while next_page:
        response = client.get_repositories(next_url=response.get('next'), workspace=workspace, params={'pagelen': 50})
        repos.extend(response.get('values'))
        if not response.get('next'):
            next_page = False
    logging.info('{} repositories found in {}'.format(len(repos), workspace))
    return repos


def get_workspaces(client: Client) -> list:
    response = client.get_workspaces(params={'pagelen': 50})
    workspaces = response.get('values')
    return workspaces


def read_config():
    config = configparser.ConfigParser()
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "config.ini")
    config.read(config_file)
    return config


def main(interactive: bool):
    conf = read_config()
    bb = None
    clone_protocol = 'ssh'
    style = Style.from_dict(
        {
            "input": "#89C713",
            "output": "#132FC7",
            "normal": "#fcfcfc",
            "warn": "#ff0066",
            "info": "#1389C7",
        }
    )

    if not interactive:
        if not 'bitbucket' in conf.sections():
            print("[bitbucket] section is missing in config file")
            exit(1)
        user = conf['bitbucket']['user']
        password = conf['bitbucket']['password']
        workspace = conf['bitbucket']['workspace']
        destination_path = None
        if 'git' in conf.sections():
            destination_path = conf['git']['destination_path']
        try:
            bb = Client(user=user, password=password)
            workspaces = get_workspaces(bb)
            slugs = [s.get('slug') for s in workspaces if s.get('slug')]
            if workspace not in slugs:
                raise NotFoundError
            if not os.path.isdir(destination_path):
                raise DestinationPathError
        except NotAuthenticatedError:
            text_fragments = FormattedText([
                    ("class:warn", "Invalid Credentials... ")])
            print_formatted_text(text_fragments, style=style)

            exit(1)
        except NotFoundError:
            text_fragments = FormattedText([
                    ("class:warn", "Invalid Workspace... ")])
            print_formatted_text(text_fragments, style=style)

            exit(1)
    else:
        user = prompt(FormattedText([("class:input", "bitbucket user: ")]), style=style)
        password = prompt(FormattedText([("class:input", "bitbucket password: ")]), style=style, is_password=True)
        try:
            bb = Client(user=user, password=password)
            workspaces = get_workspaces(bb)
            slugs = [s.get('slug') for s in workspaces if s.get('slug')]
            text_fragments = FormattedText(
                [
                    ("class:input", "workspace ("),
                    ("class:info", ', '.join(slugs)),
                    ("class:input", "): "),
                ]
            )
            workspace = prompt(text_fragments, style=style)
            if workspace not in slugs:
                raise NotFoundError
            destination_path = prompt(FormattedText([("class:input", "destination path: ")]), style=style)
            if not os.path.isdir(destination_path):
                raise DestinationPathError
            #clone_protocol = prompt(FormattedText([("class:input", "clone protocol (*ssh, https): ")]), default='ssh', style=style)
            print_formatted_text(FormattedText([("class:input", "clone protocol (*ssh, https): ssh")]), style=style)
        except NotAuthenticatedError:
            text_fragments = FormattedText([
                    ("class:warn", "Invalid Credentials... ")])
            print_formatted_text(text_fragments, style=style)
            exit(1)
        except NotFoundError:
            print_formatted_text(FormattedText([("class:warn", "Invalid Workspace... ")]), style=style)

            exit(1)
        except DestinationPathError:
            print_formatted_text(FormattedText([("class:warn", "Invalid Destination path, it must be a directory that exists. ")]), style=style)
            exit(1)

    logging.info('Starting')
    repos = get_all_repos(bb, workspace)
    stats = clone_repo_list(repos, clone_protocol, destination_path)
    print_formatted_text(FormattedText([("class:info", "========= Stats =========")]), style=style)
    for key, value in stats.items():
        text_fragments = FormattedText([
            ("class:input", key),
            ("class:input", ': '),
            ("class:info", str(value)),
        ])
        print_formatted_text(text_fragments, style=style)
    logging.info('End')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clone all repositories from bitbucket.')
    parser.add_argument('-i', '--interactive', action='store_true', help='Start in interactive mode bypassing config.ini')
    args = parser.parse_args()
    try:
        main(args.interactive)
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            exit(0)

    exit(0)

