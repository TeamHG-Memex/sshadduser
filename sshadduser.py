import grp
from io import StringIO
import logging
import os
import pwd
import random
import string
import subprocess
import sys
import tempfile

import click


format_ = '[%(levelname)s] %(filename)s:%(lineno)d %(message)s'
logging.basicConfig(format=format_)
logger = logging.getLogger()


@click.command()
@click.argument('username', required=True)
@click.argument('groups', required=False, nargs=-1)
@click.version_option()
@click.option('-v', '--verbosity', default='warning',
              help='Verbosity: error, warning, info, or debug')
def main(username, groups, verbosity):
    '''
    sshadduser: grant SSH access in a single step.

    USERNAME is the name of the user you wish to create. You may optionally list
    one or more supplemental GROUPS to add that user to (separated by spaces),
    such as sudo or wheel.

    The SSH public keys are read from STDIN, one per line, terminated by a blank
    line.

    You should run this script as root.
    '''

    logger.setLevel(_str_to_log_level(verbosity))

    try:
        if (os.geteuid() != 0):
            raise click.ClickException('You must run this tool as root.')

        _check_username(username)
        _check_groups(groups)
        password = _get_password()
        ssh_keys = _get_ssh_keys()
        _wait_for(_useradd(username, groups))
        _wait_for(_chpasswd(username, password))
        _add_authorized_keys(username, ssh_keys)

        msg = 'Created an account named {} with password {} and {} SSH key{}.'
        msg_args = [
            username,
            password,
            len(ssh_keys),
            '' if len(ssh_keys) == 1 else 's'
        ]
        click.secho(msg.format(*msg_args), fg='green')

        if len(groups) == 0:
            msg = 'Did not any supplemental groups.'
            msg_args = []
        else:
            msg = 'Added supplemental group{}: {}.'
            msg_args = ['' if len(groups) == 1 else 's', _commas(groups)]
        click.secho(msg.format(*msg_args), fg='green')
    except click.ClickException as ce:
        click.secho('Error: {}'.format(ce), fg='red', err=True)
        sys.exit(1)


def _add_authorized_keys(username, ssh_keys):
    '''
    Create or append ``ssh_keys`` to the user's ``authorized_keys`` file.
    '''

    user = pwd.getpwnam(username)
    ssh_dir = os.path.join(user.pw_dir, '.ssh')
    authorized_keys_path = os.path.join(ssh_dir, 'authorized_keys')

    try:
        logger.debug('Creating ~/.ssh directory.')
        os.mkdir(ssh_dir)
        os.chown(ssh_dir, user.pw_uid, user.pw_gid)
        os.chmod(ssh_dir, 0o700)
    except FileExistsError:
        pass

    fix_perms = not os.path.exists(authorized_keys_path)

    logger.debug('Appending SSH keys to authorized_keys.')
    with open(authorized_keys_path, 'w+') as authorized_keys:
        for ssh_key in ssh_keys:
            authorized_keys.write(ssh_key)
            authorized_keys.write('\n')

    if fix_perms:
        logger.debug('Setting owner/permissions on authorized_keys.')
        os.chown(authorized_keys_path, user.pw_uid, user.pw_gid)
        os.chmod(authorized_keys_path, 0o600)


def _check_groups(groups):
    '''
    Ensure that all of the ``groups`` exist.

    Raises exception if any group does not exist.
    '''

    for group in groups:
        logger.debug('Checking if group "{}" exists.'.format(group))

        try:
            grp.getgrnam(group)
        except KeyError:
            msg = 'Group "{}" does not exist.'.format(group)
            raise click.ClickException(msg)

        logger.debug('Group "{}" exists.'.format(group))


def _check_username(username):
    '''
    Ensure that ``username`` does not already exist.

    Raises exception if it does.
    '''

    logger.debug('Checking if username "{}"" exists.'.format(username))

    try:
        pwd.getpwnam(username)
        msg = 'Username "{}" already exists.'.format(username)
        raise click.ClickException(msg)
    except KeyError:
        pass

    logger.debug('Username "{}" does not exist.'.format(username))


def _chpasswd(username, password):
    '''
    Set password using ``chpasswd``.

    I don't think that ``chpasswd`` is POSIX compliant but I can't find any
    compliant alternative.
    '''

    process = subprocess.Popen(
        ['chpasswd'],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    credentials = '{}:{}'.format(username, password)
    process.communicate(credentials.encode('ascii'))
    return process


def _commas(list_):
    ''' Return an English comma-delimited list. '''

    if len(list_) == 1:
        return str(list_[0])
    elif len(list_) == 2:
        return '{} and {}'.format(*list_)
    elif len(list_) > 2:
        return ', '.join(list_[:-1]) + ', and {}'.format(list_[-1])
    else:
        raise ValueError('_commas() requires at least one list item.')


def _get_password(length=12):
    '''
    Prompt for a password. If it's blank, then generate a random password.
    '''

    logger.debug('Asking for a password.')

    if sys.stdin.isatty:
        click.secho(
            'Enter a password (or leave blank to generate random password):',
            fg='green'
        )

    password = sys.stdin.readline().strip()

    if password == '':
        charset = string.ascii_uppercase + \
                  string.ascii_lowercase + \
                  string.digits
        rng = random.SystemRandom()
        password = ''.join(rng.choice(charset) for _ in range(length))
        logger.debug('Generated a random password.')
    else:
        logger.debug('Got a password.')

    return password


def _get_ssh_keys():
    '''
    Prompt for SSH keys, one per line, on stdin. A blank line terminates.

    Keys are returned as a list.
    '''

    logger.debug('Asking for SSH keys.')

    if sys.stdin.isatty:
        click.secho(
            'Enter SSH keys one per line. A blank line terminates.',
            fg='green'
        )

    ssh_keys = list()

    for line in sys.stdin:
        line = line.strip()
        if line == '':
            break
        if not line.startswith('ssh-'):
            msg = 'This does not look like an OpenSSH public key: {}'
            raise click.ClickException(msg.format(line))
        ssh_keys.append(line)

    logger.debug('SSH keys: got {} lines.'.format(len(ssh_keys)))
    return ssh_keys


def _str_to_log_level(log_level_str):
    ''' Given a string like `warning`, return the corresponding log level. '''

    try:
        return getattr(logging, log_level_str.upper())
    except AttributeError:
        msg = 'Invalid log level: {}'.format(log_level_str)
        raise click.ClickException(msg)


def _wait_for(process):
    ''' Wait for ``process`` to finish and check the exit code. '''

    process.wait()

    if process.returncode != 0:
        msg = 'failed to run external tool "{}" (exit {}):\n{}'

        params = (
            process.args[0],
            process.returncode,
            process.stderr.read().decode('utf8')
        )

        raise click.ClickException(msg.format(*params))


def _useradd(username, groups):
    ''' Use POSIX ``useradd`` to add the requested user. '''

    command = [
        'useradd',
        '--create-home',
        '--groups', ','.join(groups),
        username
    ]

    return subprocess.Popen(command, stderr=subprocess.PIPE)


if __name__ == '__main__':
    main()
