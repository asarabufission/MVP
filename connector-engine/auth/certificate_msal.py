"""certificate_msal — Microsoft 365: MSAL client-credential flow with a PEM cert.

The "escape hatch" strategy from the build plan: identical prepare() shape as the
other strategies, but it wraps the MSAL library and does certificate crypto
inside. It acquires a Bearer token for Microsoft Graph using an uploaded PEM
(certificate + private key). No client secret.

`msal` and `cryptography` are imported lazily so the rest of the engine loads
without them; a clear AuthError is raised if a real Graph run is attempted
without the dependencies installed (pip install msal cryptography).
"""

from __future__ import annotations

from typing import Any

from errors import AuthError, ManifestError
from http_client import HttpClient
from resolver import resolve

from .registry import AuthResult, register


@register("certificate_msal")
class CertificateMsal:
    def prepare(
        self,
        auth_cfg: dict[str, Any],
        context: dict[str, Any],
        http: HttpClient,  # noqa: ARG002 — token via MSAL, not the engine HttpClient
    ) -> AuthResult:
        tenant_id = resolve(auth_cfg.get("tenant_id", ""), context)
        client_id = resolve(auth_cfg.get("client_id", ""), context)
        if not tenant_id or not client_id:
            raise ManifestError("certificate_msal requires tenant_id and client_id")

        cert_cfg = auth_cfg.get("certificate") or {}
        cert_ref = cert_cfg.get("from")
        if not cert_ref:
            raise ManifestError("certificate_msal requires certificate.from")
        # certificate.from is a dotted path into context, e.g. credentials.certificate_pem
        pem = resolve("{" + str(cert_ref) + "}", context)
        if not pem:
            raise ManifestError(f"certificate_msal: no PEM found at {cert_ref!r}")

        scopes = resolve(
            auth_cfg.get("scopes") or ["https://graph.microsoft.com/.default"],
            context,
        )

        try:
            import msal
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes
        except ImportError as exc:
            raise AuthError(
                "certificate_msal requires the 'msal' and 'cryptography' packages "
                "(pip install msal cryptography)"
            ) from exc

        pem_text = pem if isinstance(pem, str) else pem.decode("utf-8")
        try:
            cert = x509.load_pem_x509_certificate(pem_text.encode("utf-8"))
            thumbprint = cert.fingerprint(hashes.SHA1()).hex()
        except Exception as exc:  # noqa: BLE001
            raise AuthError(
                f"certificate_msal: could not parse PEM certificate: {exc}"
            ) from exc

        app = msal.ConfidentialClientApplication(
            client_id=str(client_id),
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential={
                "private_key": pem_text,
                "thumbprint": thumbprint,
                "public_certificate": pem_text,
            },
        )
        result = app.acquire_token_for_client(scopes=list(scopes))
        token = result.get("access_token")
        if not token:
            detail = result.get("error_description") or result.get("error") or "unknown error"
            raise AuthError(f"certificate_msal token request failed: {detail}")
        if not isinstance(token, str):
            raise AuthError("certificate_msal: access token must be a string")

        placement = auth_cfg.get("token_placement") or {}
        header_value = placement.get("template", "Bearer {access_token}").format(
            access_token=token
        )
        name = placement.get("name", "Authorization")
        return AuthResult(headers={name: header_value}, access_token=token)
