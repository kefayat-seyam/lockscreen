import hashlib
import json
import socket
import ssl
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


class LinkScreenMobile(App):
    def build(self):
        self.title = "LinkScreen"
        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))

        title = Label(text="[b]LinkScreen[/b]", markup=True, font_size="28sp",
                      size_hint_y=None, height=dp(55))
        subtitle = Label(text="Connect your phone to your Windows PC",
                         size_hint_y=None, height=dp(42))
        self.host = TextInput(hint_text="Windows PC IPv4 address (e.g. 192.168.1.10)",
                              multiline=False, size_hint_y=None, height=dp(50))
        self.port = TextInput(text="8765", hint_text="Port",
                              multiline=False, input_filter="int",
                              size_hint_y=None, height=dp(50))
        self.fingerprint = TextInput(
            hint_text="Paste desktop TLS SHA-256 fingerprint (64 hex characters)",
            multiline=False, size_hint_y=None, height=dp(80))
        self.status = Label(text="Not connected", size_hint_y=None, height=dp(55))
        self.connect_button = Button(text="Connect securely",
                                     size_hint_y=None, height=dp(55))
        self.connect_button.bind(on_release=self.connect)

        root.add_widget(title)
        root.add_widget(subtitle)
        root.add_widget(self.host)
        root.add_widget(self.port)
        root.add_widget(self.fingerprint)
        root.add_widget(self.connect_button)
        root.add_widget(self.status)
        root.add_widget(Label(
            text="Development prototype. Use only on a trusted private Wi-Fi network.",
            size_hint_y=None, height=dp(55)
        ))
        return root

    def set_status(self, message):
        self.status.text = message
        self.connect_button.disabled = False

    def connect(self, *_):
        host = self.host.text.strip()
        fp = self.fingerprint.text.strip().replace(":", "").lower()
        try:
            port = int(self.port.text.strip())
        except ValueError:
            self.status.text = "Enter a valid port."
            return

        if not host or len(fp) != 64:
            self.status.text = "Enter the PC address and 64-character fingerprint."
            return
        try:
            int(fp, 16)
        except ValueError:
            self.status.text = "Fingerprint must contain hexadecimal characters."
            return

        self.connect_button.disabled = True
        self.status.text = "Connecting..."
        threading.Thread(target=self._connect_worker,
                         args=(host, port, fp), daemon=True).start()

    def _connect_worker(self, host, port, expected_fp):
        try:
            # TLS certificate is verified by explicit SHA-256 pinning below.
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((host, port), timeout=8) as raw:
                with context.wrap_socket(raw, server_hostname="LinkScreen") as conn:
                    actual_fp = hashlib.sha256(
                        conn.getpeercert(binary_form=True)
                    ).hexdigest()
                    if actual_fp.lower() != expected_fp:
                        raise ssl.SSLError(
                            "Certificate fingerprint mismatch. Verify the PC fingerprint."
                        )

                    hello = {
                        "type": "hello",
                        "device_name": "Android LinkScreen"
                    }
                    conn.sendall((json.dumps(hello) + "\n").encode("utf-8"))
                    response = conn.makefile("rb").readline(4096)
                    message = json.loads(response.decode("utf-8"))
                    if message.get("type") != "welcome":
                        raise ValueError("Unexpected server response")
                    result = "Connected securely. Handshake successful."
        except Exception as exc:
            result = f"Connection failed: {exc}"

        Clock.schedule_once(lambda _dt: self.set_status(result), 0)


if __name__ == "__main__":
    LinkScreenMobile().run()
