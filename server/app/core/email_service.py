import asyncio
import datetime
import io
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import qrcode
from server.app.core.config import settings

logger = logging.getLogger("server.email")


class EmailService:
    @staticmethod
    def is_smtp_configured() -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)

    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Kirim email via SMTP atau log ke terminal jika belum dikonfigurasi."""
        if not to_email:
            logger.warning("[Email] Alamat email tujuan kosong, pesan dibatalkan.")
            return False

        if cls.is_smtp_configured():
            try:
                await asyncio.to_thread(
                    cls._send_smtp_sync,
                    to_email=to_email,
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content,
                    attachments=attachments,
                )
                logger.info(f"[Email] Berhasil dikirim ke {to_email}: '{subject}'")
                return True
            except Exception as e:
                logger.error(f"[Email] Gagal mengirim email via SMTP: {e}. Menggunakan log fallback.")

        # Fallback terminal log (sangat berguna untuk development & jika SMTP belum diisi)
        print("\n" + "=" * 65)
        print("  [NEXA HOME EMAIL SERVICE - PENGIRIMAN PESAN]")
        print(f"  Kepada  : {to_email}")
        print(f"  Subjek  : {subject}")
        print("  " + "-" * 61)
        for line in text_content.strip().split("\n"):
            print(f"  {line}")
        if attachments:
            print(f"  [Lampiran: {len(attachments)} file disertakan]")
        print("=" * 65 + "\n")
        return True

    @classmethod
    def _send_smtp_sync(
        cls,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ):
        msg = MIMEMultipart("mixed")
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        body_part = MIMEMultipart("alternative")
        body_part.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            body_part.attach(MIMEText(html_content, "html", "utf-8"))
        msg.attach(body_part)

        if attachments:
            for att in attachments:
                part = MIMEApplication(att["content"], Name=att.get("filename", "attachment"))
                part["Content-Disposition"] = f'attachment; filename="{att.get("filename", "attachment")}"'
                msg.attach(part)

        port = settings.SMTP_PORT
        if port == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=15) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, port, timeout=15) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

    @classmethod
    async def send_otp_email(cls, to_email: str, otp_code: str, purpose: str = "password_reset") -> bool:
        """Kirim kode 6 digit OTP untuk lupa kata sandi atau verifikasi."""
        if purpose == "password_reset":
            subject = "Kode Pemulihan Kata Sandi Nexa Home"
            text_body = (
                f"Halo,\n\n"
                f"Anda telah meminta pemulihan kata sandi untuk akun Nexa Home Anda.\n\n"
                f"Kode OTP Anda: {otp_code}\n\n"
                f"Kode ini berlaku selama 15 menit. JANGAN bagikan kode ini kepada siapa pun.\n"
                f"Jika Anda tidak merasa meminta ini, abaikan email ini.\n\n"
                f"Salam,\nTim Nexa Home"
            )
            html_body = f"""
            <div style="font-family: Arial, sans-serif; background-color: #151816; color: #FFFFFF; padding: 24px; border-radius: 8px;">
                <h2 style="color: #5FA08E; margin-bottom: 8px;">Nexa Home — Pemulihan Kata Sandi</h2>
                <p style="color: #A0A5A2;">Gunakan kode verifikasi berikut untuk memperbarui kata sandi akun Anda:</p>
                <div style="background-color: #1D211E; border: 1px solid #2B302C; padding: 16px; border-radius: 6px; text-align: center; margin: 20px 0;">
                    <span style="font-family: monospace; font-size: 32px; letter-spacing: 6px; font-weight: bold; color: #5FA08E;">{otp_code}</span>
                </div>
                <p style="color: #A0A5A2; font-size: 13px;">Kode ini berlaku selama 15 menit. Jangan berikan kode ini kepada siapapun.</p>
                <hr style="border: none; border-top: 1px solid #2B302C; margin: 20px 0;" />
                <p style="color: #6C726E; font-size: 11px;">Sistem Smart Home & Pengawasan Keluarga — {settings.BASE_PUBLIC_URL}</p>
            </div>
            """
        else:
            subject = "Kode Verifikasi Nexa Home"
            text_body = f"Kode verifikasi akun Anda: {otp_code} (Berlaku 15 menit)."
            html_body = f"<p>Kode verifikasi akun Anda: <b>{otp_code}</b></p>"

        return await cls.send_email(to_email, subject, text_body, html_body)

    @classmethod
    async def send_login_alert_email(
        cls,
        to_email: str,
        username: str,
        ip_address: str,
        user_agent: str = "Browser / Aplikasi Nexa Home",
        login_time: Optional[str] = None,
    ) -> bool:
        """Kirim notifikasi email bahwa ada sesi login baru pada akun."""
        time_str = login_time or datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        subject = f"Peringatan Keamanan: Login Baru Terdeteksi ({username})"
        text_body = (
            f"Halo {username},\n\n"
            f"Sistem Nexa Home mendeteksi adanya aktivitas masuk (login) baru ke akun Anda.\n\n"
            f"Waktu       : {time_str}\n"
            f"Alamat IP   : {ip_address}\n"
            f"Perangkat   : {user_agent}\n\n"
            f"Jika ini adalah Anda, Anda dapat mengabaikan email ini.\n"
            f"Jika Anda TIDAK merasa melakukan login ini, segera buka menu Pengaturan atau lakukan reset kata sandi.\n\n"
            f"Salam,\nKeamanan Nexa Home"
        )
        html_body = f"""
        <div style="font-family: Arial, sans-serif; background-color: #151816; color: #FFFFFF; padding: 24px; border-radius: 8px;">
            <h2 style="color: #5FA08E; margin-bottom: 8px;">Nexa Home — Peringatan Login Baru</h2>
            <p style="color: #A0A5A2;">Aktivitas masuk baru terdeteksi pada akun <b>{username}</b>:</p>
            <table style="color: #FFFFFF; font-size: 14px; margin: 16px 0; border-collapse: collapse; width: 100%;">
                <tr style="border-bottom: 1px solid #2B302C;"><td style="padding: 8px 0; color: #A0A5A2;">Waktu</td><td style="padding: 8px 0; font-family: monospace;">{time_str}</td></tr>
                <tr style="border-bottom: 1px solid #2B302C;"><td style="padding: 8px 0; color: #A0A5A2;">Alamat IP</td><td style="padding: 8px 0; font-family: monospace; color: #5FA08E;">{ip_address}</td></tr>
                <tr style="border-bottom: 1px solid #2B302C;"><td style="padding: 8px 0; color: #A0A5A2;">Perangkat</td><td style="padding: 8px 0;">{user_agent}</td></tr>
            </table>
            <p style="color: #E24A4A; font-size: 13px;">Jika ini bukan Anda, segera ubah kata sandi dan periksa sesi akun Anda di Pengaturan.</p>
            <hr style="border: none; border-top: 1px solid #2B302C; margin: 20px 0;" />
            <p style="color: #6C726E; font-size: 11px;">Sistem Smart Home & Pengawasan Keluarga — {settings.BASE_PUBLIC_URL}</p>
        </div>
        """
        return await cls.send_email(to_email, subject, text_body, html_body)

    @classmethod
    async def send_device_qr_email(
        cls,
        to_email: str,
        device_id: str,
        claim_token: str,
        pairing_code: Optional[str] = None,
    ) -> bool:
        """Kirim gambar QR pairing dan token klaim perangkat ke email pengguna."""
        qr_data = f"nexa://claim?device_id={device_id}&token={claim_token}"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_bytes = buf.getvalue()

        subject = f"Backup Akses & QR Code Perangkat — {device_id}"
        text_body = (
            f"Halo,\n\n"
            f"Berikut adalah data pairing & kode klaim untuk perangkat Nexa Home Anda:\n\n"
            f"ID Perangkat  : {device_id}\n"
            f"Token Klaim   : {claim_token}\n"
        )
        if pairing_code:
            text_body += f"Kode Pairing  : {pairing_code}\n"
        text_body += (
            f"\nLampiran email ini berisi gambar QR Code yang dapat langsung di-scan dari aplikasi Nexa Home.\n\n"
            f"Simpan email ini dengan aman sebagai arsip pemulihan perangkat Anda.\n\n"
            f"Salam,\nNexa Home"
        )

        html_body = f"""
        <div style="font-family: Arial, sans-serif; background-color: #151816; color: #FFFFFF; padding: 24px; border-radius: 8px;">
            <h2 style="color: #5FA08E; margin-bottom: 8px;">Nexa Home — QR Code Perangkat</h2>
            <p style="color: #A0A5A2;">Data pairing dan kode klaim untuk perangkat Anda:</p>
            <table style="color: #FFFFFF; font-size: 14px; margin: 16px 0; border-collapse: collapse;">
                <tr><td style="padding: 6px 12px; color: #A0A5A2;">ID Perangkat</td><td style="padding: 6px 12px; font-weight: bold;">{device_id}</td></tr>
                <tr><td style="padding: 6px 12px; color: #A0A5A2;">Token Klaim</td><td style="padding: 6px 12px; font-family: monospace; color: #5FA08E;">{claim_token}</td></tr>
                {f'<tr><td style="padding: 6px 12px; color: #A0A5A2;">Kode Pairing</td><td style="padding: 6px 12px; font-weight: bold;">{pairing_code}</td></tr>' if pairing_code else ''}
            </table>
            <p style="color: #A0A5A2; font-size: 13px;">Gambar QR Code telah dilampirkan pada email ini untuk di-scan dari aplikasi Nexa Home.</p>
        </div>
        """

        attachments = [
            {
                "filename": f"qrcode_{device_id}.png",
                "content": qr_bytes,
                "mime_type": "image/png",
            }
        ]
        return await cls.send_email(to_email, subject, text_body, html_body, attachments=attachments)


email_service = EmailService()
