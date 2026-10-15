import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx

from server.app.core.config import settings
from server.app.core.assistant.tools import ASSISTANT_TOOLS_SCHEMA

logger = logging.getLogger("server.assistant.deepseek")


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.DEEPSEEK_API_KEY
        self.base_url = (base_url or settings.DEEPSEEK_BASE_URL).rstrip("/")
        self.model = model or settings.DEEPSEEK_MODEL

    def is_configured(self) -> bool:
        if not self.api_key or not self.api_key.strip():
            return False
        if "your_" in self.api_key or "change_me" in self.api_key or self.api_key == "test_key":
            return False
        return True

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int | None = None,
    ) -> Dict[str, Any]:
        """Memanggil DeepSeek Chat Completion secara non-streaming."""
        if not self.is_configured():
            raise ConnectionError("DEEPSEEK_API_KEY belum dikonfigurasi di server .env.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or settings.ASSISTANT_MAX_TOKENS,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"DeepSeek API error {resp.status_code}: {resp.text}"
                )
            data = resp.json()
            return data["choices"][0]["message"]

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming chat completion dengan DeepSeek via SSE.
        Yields chunk objek berisi {'type': 'token' | 'tool_call', ...}
        """
        if not self.is_configured():
            raise ConnectionError("DEEPSEEK_API_KEY belum dikonfigurasi di server .env.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or settings.ASSISTANT_MAX_TOKENS,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools

        start_time = time.perf_counter()
        first_token_time: Optional[float] = None

        async with httpx.AsyncClient(timeout=45.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    err_body = await resp.aread()
                    raise RuntimeError(f"DeepSeek API error {resp.status_code}: {err_body.decode('utf-8', errors='ignore')}")

                accumulated_tool_calls: Dict[int, Dict[str, Any]] = {}

                async for line in resp.aiter_lines():
                    clean_line = line.strip()
                    if not clean_line or clean_line == "data: [DONE]":
                        continue
                    if clean_line.startswith("data: "):
                        data_str = clean_line[6:].strip()
                        try:
                            chunk_data = json.loads(data_str)
                            choice = chunk_data.get("choices", [{}])[0]
                            delta = choice.get("delta", {})

                            # Content tokens
                            if "content" in delta and delta["content"]:
                                if first_token_time is None:
                                    first_token_time = time.perf_counter()
                                    ttft = first_token_time - start_time
                                    yield {"type": "ttft", "seconds": ttft}
                                yield {"type": "token", "content": delta["content"]}

                            # Tool calls delta
                            if "tool_calls" in delta:
                                for tc in delta["tool_calls"]:
                                    idx = tc.get("index", 0)
                                    if idx not in accumulated_tool_calls:
                                        accumulated_tool_calls[idx] = {
                                            "id": tc.get("id", ""),
                                            "name": tc.get("function", {}).get("name", ""),
                                            "arguments": "",
                                        }
                                    fn = tc.get("function", {})
                                    if "name" in fn and fn["name"]:
                                        accumulated_tool_calls[idx]["name"] = fn["name"]
                                    if "arguments" in fn and fn["arguments"]:
                                        accumulated_tool_calls[idx]["arguments"] += fn["arguments"]

                        except Exception as exc:
                            logger.debug(f"Error parsing SSE chunk: {exc}")

                # Jika ada tool calls terakumulasi
                if accumulated_tool_calls:
                    for idx, tc in sorted(accumulated_tool_calls.items()):
                        try:
                            parsed_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except Exception:
                            parsed_args = {"raw": tc["arguments"]}
                        yield {
                            "type": "tool_call",
                            "id": tc["id"],
                            "name": tc["name"],
                            "arguments": parsed_args,
                        }
