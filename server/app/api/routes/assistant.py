import json
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.api.deps import get_current_user
from server.app.core.assistant.service import AssistantService
from server.app.core.database import get_db
from server.app.core.tts.service import get_tts_service
from server.app.models.user import User

router = APIRouter(prefix="/assistant", tags=["assistant"])
assistant_service = AssistantService()


# --- Pydantic Schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)


class ConfirmActionRequest(BaseModel):
    confirmation_id: str = Field(..., min_length=10, max_length=40)
    confirmed: bool = True


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    voice: Optional[str] = None
    provider: Optional[Literal["edge-tts", "piper"]] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


# --- Endpoints ---

@router.post("/chat")
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kirim pesan teks ke asisten (non-streaming response)."""
    full_text = ""
    confirmation_data = None
    item_data = None
    ttft_val = None

    async for chunk in assistant_service.stream_chat(db, current_user, payload.message):
        c_type = chunk.get("type")
        if c_type == "ttft":
            ttft_val = chunk.get("seconds")
        elif c_type == "token":
            full_text += chunk.get("content", "")
        elif c_type == "confirmation_required":
            confirmation_data = chunk
        elif c_type == "item_found":
            item_data = chunk.get("data")
        elif c_type == "error":
            raise HTTPException(status_code=400, detail=chunk.get("message"))

    return {
        "reply": full_text.strip(),
        "confirmation": confirmation_data,
        "item_data": item_data,
        "ttft_seconds": ttft_val,
    }


@router.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Streaming chat completion dengan SSE (Server-Sent Events)."""

    async def event_generator():
        async for chunk in assistant_service.stream_chat(db, current_user, payload.message):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/confirm")
async def confirm_action(
    payload: ConfirmActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mengonfirmasi (Ya) atau membatalkan (Batal) aksi sensitif."""
    res = await assistant_service.confirm_action(
        db, payload.confirmation_id, payload.confirmed, current_user
    )
    if "error" in res:
        status_code = res.get("status", 400)
        raise HTTPException(status_code=status_code, detail=res["error"])
    return res


@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mengambil riwayat percakapan pengguna saat ini."""
    messages = await assistant_service.get_recent_history(db, current_user.id, limit=limit)
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.delete("/history")
async def delete_chat_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Menghapus seluruh riwayat percakapan pengguna secara permanen."""
    deleted_count = await assistant_service.clear_history(db, current_user.id)
    return {"message": "Riwayat percakapan berhasil dihapus.", "deleted_count": deleted_count}


@router.post("/tts")
async def synthesize_speech(
    payload: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Sintesis suara dari teks dengan cache disk dan auto-fallback.
    Maksimal 500 karakter.
    """
    tts_service = get_tts_service()
    try:
        audio_bytes, mime_type, prov_used, elapsed = await tts_service.synthesize(
            text=payload.text,
            preferred_provider=payload.provider,
            voice=payload.voice,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sintesis suara gagal: {exc}")

    return Response(
        content=audio_bytes,
        media_type=mime_type,
        headers={
            "X-TTS-Provider": prov_used,
            "X-TTS-Elapsed": f"{elapsed:.3f}",
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.get("/tts")
async def synthesize_speech_get(
    text: str = Query(..., min_length=1, max_length=500),
    voice: Optional[str] = Query(None),
    provider: Optional[Literal["edge-tts", "piper"]] = Query(None),
):
    """Sintesis suara via GET query untuk kemudahan audio streaming player."""
    tts_service = get_tts_service()
    try:
        audio_bytes, mime_type, prov_used, elapsed = await tts_service.synthesize(
            text=text,
            preferred_provider=provider,
            voice=voice,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sintesis suara gagal: {exc}")

    return Response(
        content=audio_bytes,
        media_type=mime_type,
        headers={
            "X-TTS-Provider": prov_used,
            "X-TTS-Elapsed": f"{elapsed:.3f}",
            "Cache-Control": "public, max-age=86400",
        },
    )



@router.get("/tts/voices")
async def get_available_voices(
    current_user: User = Depends(get_current_user),
):
    """Daftar pilihan suara TTS yang didukung."""
    return [
        {
            "id": "id-ID-ArdiNeural",
            "name": "Ardi (Pria)",
            "provider": "edge-tts",
            "description": "Suara jernih Bahasa Indonesia (Online)",
        },
        {
            "id": "id-ID-GadisNeural",
            "name": "Gadis (Wanita)",
            "provider": "edge-tts",
            "description": "Suara ramah Bahasa Indonesia (Online)",
        },
        {
            "id": "id_ID-indotts-medium",
            "name": "Piper Indonesia (Offline)",
            "provider": "piper",
            "description": "Suara lokal tanpa koneksi internet",
        },
    ]
