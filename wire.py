"""Small JSON-over-local-UNIX-socket demo protocol; no network services."""
import hashlib
import hmac
import json
import socket
import uuid

MAX_MESSAGE = 32768


def canonical(obj):
    return json.dumps(obj, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode()


def signature(key, body):
    return hmac.new(bytes.fromhex(key), canonical(body), hashlib.sha256).hexdigest()


def signed(caller, key, request, nonce=None):
    body = {'caller': caller, 'nonce': nonce or str(uuid.uuid4()), 'request': request}
    return {**body, 'signature': signature(key, body)}


def exchange(socket_path, message, timeout=3.0):
    payload = canonical(message) + b'\n'
    if len(payload) > MAX_MESSAGE:
        raise ValueError('Request too large')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(timeout)
        conn.connect(socket_path)
        conn.sendall(payload)
        buf = b''
        while b'\n' not in buf:
            part = conn.recv(4096)
            if not part:
                raise RuntimeError('Server closed without reply')
            buf += part
            if len(buf) > MAX_MESSAGE:
                raise ValueError('Reply too large')
    return json.loads(buf.split(b'\n', 1)[0])
