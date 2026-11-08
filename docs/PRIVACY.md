# Privacy notes

Current prototype:
- Does not capture the desktop.
- Does not record or store screen content.
- Does not require a cloud account or cloud relay.
- Uses TLS with explicit certificate fingerprint pinning.
- Listens on the local network interface on TCP port 8765 while started.

Limitations:
- Pairing approval UI, revocation, rate limiting, and production security review are not yet implemented.
- Use only on a trusted private Wi-Fi network.
- Do not expose the listening port to the public internet.
- The self-signed private key is stored locally under `runtime/` and must never be committed.
