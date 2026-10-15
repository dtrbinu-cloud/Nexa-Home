import logging
import os
import sys
from typing import Any, Dict, Optional
import httpx
from server.app.core.config import settings

logger = logging.getLogger("server.google_auth")


class GoogleAuthService:
    @staticmethod
    def get_auth_url(redirect_uri: str, state: Optional[str] = None) -> str:
        """Menghasilkan URL consent Google OAuth2."""
        client_id = settings.GOOGLE_CLIENT_ID
        scope = "openid email profile"
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = [
            f"client_id={client_id}",
            f"redirect_uri={redirect_uri}",
            "response_type=code",
            f"scope={scope.replace(' ', '%20')}",
            "access_type=offline",
            "prompt=select_account",
        ]
        if state:
            params.append(f"state={state}")
        return f"{base_url}?{'&'.join(params)}"

    @classmethod
    async def verify_google_credentials(
        cls,
        id_token: Optional[str] = None,
        code: Optional[str] = None,
        access_token: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verifikasi kredensial Google (ID Token, Auth Code, atau Access Token).
        Mengembalikan dict: { 'sub': str, 'email': str, 'name': str, 'email_verified': bool }
        """
        # Dukungan mock untuk pengujian otomatis (Unit Test / Dev Mock)
        if id_token and id_token.startswith("mock_google_"):
            is_testing = "pytest" in sys.modules or os.environ.get("APP_ENV") == "test" or os.environ.get("TESTING") == "true"
            if settings.GOOGLE_CLIENT_ID and not is_testing:
                raise ValueError("Dev mock token tidak diizinkan saat GOOGLE_CLIENT_ID aktif di luar pengujian.")

            email_part = id_token.replace("mock_google_", "")
            if "@" not in email_part:
                email_part = f"{email_part}@gmail.com"
            return {
                "sub": f"google_sub_{abs(hash(email_part)) % 1000000}",
                "email": email_part.lower(),
                "name": email_part.split("@")[0].title(),
                "email_verified": True,
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Jika menerima Auth Code dari redirect flow
            if code:
                token_url = "https://oauth2.googleapis.com/token"
                r_token = await client.post(
                    token_url,
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": redirect_uri or f"{settings.BASE_PUBLIC_URL}/login",
                        "grant_type": "authorization_code",
                    },
                )
                if r_token.status_code != 200:
                    logger.error(f"[GoogleAuth] Token exchange failed: {r_token.text}")
                    raise ValueError("Gagal menukar kode otorisasi Google.")

                token_json = r_token.json()
                id_token = token_json.get("id_token")
                access_token = token_json.get("access_token")

            # 2. Jika ada ID Token, verifikasi via endpoint resmi Google tokeninfo
            if id_token:
                verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
                res = await client.get(verify_url)
                if res.status_code != 200:
                    logger.error(f"[GoogleAuth] ID Token verification failed: {res.text}")
                    raise ValueError("ID Token Google tidak valid atau telah kedaluwarsa.")

                data = res.json()
                # Jika GOOGLE_CLIENT_ID diset, verifikasi audience
                if settings.GOOGLE_CLIENT_ID and data.get("aud") != settings.GOOGLE_CLIENT_ID:
                    logger.warning("[GoogleAuth] Client ID mismatch pada Google Token.")

                return {
                    "sub": data.get("sub"),
                    "email": data.get("email", "").lower(),
                    "name": data.get("name") or data.get("email", "").split("@")[0],
                    "email_verified": data.get("email_verified") in [True, "true", "True", 1],
                }

            # 3. Jika menggunakan Access Token langsung
            if access_token:
                userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
                res = await client.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
                if res.status_code != 200:
                    raise ValueError("Access Token Google tidak valid.")

                data = res.json()
                return {
                    "sub": data.get("sub"),
                    "email": data.get("email", "").lower(),
                    "name": data.get("name") or data.get("email", "").split("@")[0],
                    "email_verified": data.get("email_verified", True),
                }

        raise ValueError("Kredensial Google (id_token, code, atau access_token) diperlukan.")


google_auth_service = GoogleAuthService()
