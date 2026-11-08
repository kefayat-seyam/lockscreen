# Architecture

The first prototype has two Python applications.

- `desktop/`: PySide6 Windows dashboard and TLS TCP server.
- `mobile/`: Kivy Android client.
- `shared/`: reserved for the versioned protocol shared by both apps.
- `native/`: reserved for small platform-specific integrations.

The desktop generates a self-signed certificate locally. The Android client checks the certificate's SHA-256 fingerprint entered by the user before sending a JSON-line hello message.

The first milestone sends no screen content. It validates secure device-to-PC connectivity only.

Future video transport, capture, rendering, input injection, and the Windows virtual display driver will be separate components.
