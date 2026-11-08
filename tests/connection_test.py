
import socket
import ssl
import json
import hashlib

from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import serialization

HOST = "127.0.0.1"
PORT = 8765

CERT_PATH = Path("runtime/server-cert.pem")


def get_fingerprint():
    with open(CERT_PATH, "rb") as file:
        cert = x509.load_pem_x509_certificate(file.read())

    der = cert.public_bytes(serialization.Encoding.DER)
    return hashlib.sha256(der).hexdigest()


def test_connection():
    print("LinkScreen connection test")
    print("===========================")

    expected = get_fingerprint()

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((HOST, PORT), timeout=5) as raw:
            with context.wrap_socket(
                raw, server_hostname="LinkScreen"
            ) as connection:

                actual = hashlib.sha256(
                    connection.getpeercert(binary_form=True)
                ).hexdigest()

                if actual != expected:
                    raise RuntimeError("Certificate fingerprint mismatch")

                print("TLS connection established.")

                message = {
                    "type": "hello",
                    "device_name": "LinkScreen Test Client"
                }

                connection.sendall(
                    (json.dumps(message) + "\n").encode("utf-8")
                )

                response = connection.makefile("rb").readline()

                print("Server response:")
                print(response.decode("utf-8").strip())

                print("\nSUCCESS: Connection test passed!")

    except Exception as error:
        print("\nCONNECTION FAILED:")
        print(error)


if __name__ == "__main__":
    test_connection()
