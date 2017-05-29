import os
import sys
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand


DEFAULT_KEYFILE_NAME = '.secrets.key'
DEFAULT_KEY_ENVVAR = 'SECRETS_KEY'


class SecretsException(BaseException):
    pass


def cipher(key):
    k = base64.urlsafe_b64encode(_kdf_derive(key))

    return Fernet(k)


def encrypt(s, key):
    c = cipher(key)

    try:
        data = s.encode('utf-8')
        return c.encrypt(data).decode('utf-8')
    except InvalidToken:
        raise SecretsException("Invalid key")


def decrypt(s, key):
    c = cipher(key)

    try:
        data = s.encode('utf-8')
        return c.decrypt(data).decode('utf-8')
    except InvalidToken:
        raise SecretsException("Invalid key")


def genkey():
    return Fernet.generate_key().decode('utf-8')


def resolve_key(key):
    if key is not None:
        return key

    local_key = os.path.join(os.getcwd(), DEFAULT_KEYFILE_NAME)
    key = _read_file_if_exists(local_key)
    if key is not None:
        return key

    env_specified_key = os.getenv(DEFAULT_KEY_ENVVAR)
    if env_specified_key is not None:
        key = _read_file_if_exists(env_specified_key)
        if key is not None:
            return key

    user_home_key = os.path.join(os.path.expanduser('~'), DEFAULT_KEYFILE_NAME)
    key = _read_file_if_exists(user_home_key)
    if key is not None:
        return key

    return None


def _read_file_if_exists(path):
    if os.path.isfile(path):
        with open(path) as f:
            return f.read()

    return None


def _kdf_derive(key):
    kdf = HKDFExpand(
        algorithm=hashes.SHA256(),
        length=32,
        info=None,
        backend=default_backend()
    )

    return kdf.derive(key.encode('utf-8'))