import json
import socket
import ssl
import threading
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QTextEdit
)

HOST = "0.0.0.0"
PORT = 8765
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
CERT_FILE = RUNTIME / "server-cert.pem"
KEY_FILE = RUNTIME / "server-key.pem"


def ensure_local_certificate():
    """Create a self-signed TLS certificate once; private key stays local."""
    RUNTIME.mkdir(exist_ok=True)
    if CERT_FILE.exists() and KEY_FILE.exists():
        return

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "LinkScreen Local Desktop")
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ))
        .not_valid_after(__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ) + __import__("datetime").timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    KEY_FILE.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def fingerprint():
    cert = ssl.PEM_cert_to_DER_cert(CERT_FILE.read_text(encoding="ascii"))
    return __import__("hashlib").sha256(cert).hexdigest()


def local_ipv4_addresses():
    found = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = item[4][0]
            if not ip.startswith("127."):
                found.add(ip)
    except OSError:
        pass
    return sorted(found) or ["127.0.0.1"]


class ServerSignals(QObject):
    message = Signal(str)
    status = Signal(str)


class LinkServer(threading.Thread):
    def __init__(self, signals):
        super().__init__(daemon=True)
        self.signals = signals
        self.stop_event = threading.Event()
        self.server_socket = None

    def stop(self):
        self.stop_event.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass

    def run(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(str(CERT_FILE), str(KEY_FILE))

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            self.signals.status.emit(f"Listening on port {PORT}")
            self.signals.message.emit("Waiting for a LinkScreen mobile connection...")
        except OSError as exc:
            self.signals.status.emit("Server failed to start")
            self.signals.message.emit(f"Network error: {exc}")
            return

        while not self.stop_event.is_set():
            try:
                raw, address = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                with context.wrap_socket(raw, server_side=True) as conn:
                    conn.settimeout(10)
                    data = conn.makefile("rb").readline(4096)
                    request = json.loads(data.decode("utf-8"))
                    if request.get("type") != "hello":
                        raise ValueError("Unsupported handshake message")
                    device = str(request.get("device_name", "Android device"))[:80]
                    response = {
                        "type": "welcome",
                        "app": "LinkScreen",
                        "protocol_version": 1,
                        "message": "Secure handshake successful"
                    }
                    conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                    self.signals.message.emit(
                        f"Connected: {device} ({address[0]}) — TLS handshake successful"
                    )
            except Exception as exc:
                self.signals.message.emit(f"Connection rejected/ended: {exc}")
            finally:
                try:
                    raw.close()
                except Exception:
                    pass

        self.signals.status.emit("Server stopped")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkScreen Desktop — Development Build")
        self.resize(620, 470)
        self.signals = ServerSignals()
        self.server = None

        ensure_local_certificate()
        ips = "\n".join(f"  • {ip}" for ip in local_ipv4_addresses())
        fp = fingerprint()

        title = QLabel("LinkScreen")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        subtitle = QLabel("Python-first phone-to-PC connection prototype")
        address = QLabel(f"PC addresses:\n{ips}\n\nPort: {PORT}")
        address.setTextInteractionFlags(
            __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.TextInteractionFlag.TextSelectableByMouse
        )
        fingerprint_label = QLabel(
            "TLS certificate SHA-256 fingerprint:\n" + fp
        )
        fingerprint_label.setWordWrap(True)
        fingerprint_label.setTextInteractionFlags(
            __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.status = QLabel("Server not started")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.start_button = QPushButton("Start connection server")
        self.stop_button = QPushButton("Stop server")
        self.stop_button.setEnabled(False)

        layout = QVBoxLayout()
        for widget in (title, subtitle, address, fingerprint_label, self.status,
                       self.start_button, self.stop_button, QLabel("Activity"), self.log):
            layout.addWidget(widget)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        self.signals.message.connect(self.log.append)
        self.signals.status.connect(self.status.setText)

    def start_server(self):
        if self.server and self.server.is_alive():
            return
        self.server = LinkServer(self.signals)
        self.server.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_server(self):
        if self.server:
            self.server.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        self.stop_server()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
