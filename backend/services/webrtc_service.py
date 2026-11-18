"""WebRTC service for real-time continuous video streaming with Sensus AI.

Receives video tracks over WebRTC, samples frames on-the-fly, executes YOLO
and depth estimation without blocking, and streams results back over RTCDataChannel.
"""

from __future__ import annotations

import asyncio
from io import BytesIO
import json
import logging
from typing import Any

from starlette.concurrency import run_in_threadpool

from services.vision_pipeline import realtime_analyze

logger = logging.getLogger("sensus.webrtc")

try:
    from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
    from aiortc.contrib.media import MediaRelay
except ImportError:  # pragma: no cover
    MediaStreamTrack = None
    RTCPeerConnection = None
    RTCSessionDescription = None
    RTCIceCandidate = None


class WebRTCManager:
    def __init__(self) -> None:
        self.pcs: dict[str, Any] = {}
        self.data_channels: dict[str, list[Any]] = {}

    @property
    def available(self) -> bool:
        return RTCPeerConnection is not None

    async def handle_offer(self, sdp: str, sdp_type: str, session_id: str = "default") -> dict[str, str]:
        if not self.available:
            raise RuntimeError(
                "aiortc no esta instalado en el backend. "
                "Agrega 'aiortc' a requirements.txt e instalalo en el entorno."
            )

        # Close existing connection for this session if any
        if session_id in self.pcs:
            old_pc = self.pcs.pop(session_id, None)
            if old_pc:
                await old_pc.close()

        pc = RTCPeerConnection()
        self.pcs[session_id] = pc
        self.data_channels[session_id] = []

        @pc.on("datachannel")
        def on_datachannel(channel: Any) -> None:
            logger.info("WebRTC DataChannel '%s' conectado para sesion %s", channel.label, session_id)
            self.data_channels[session_id].append(channel)

            @channel.on("close")
            def on_close() -> None:
                if channel in self.data_channels.get(session_id, []):
                    self.data_channels[session_id].remove(channel)

        @pc.on("track")
        def on_track(track: Any) -> None:
            if track.kind == "video":
                logger.info("WebRTC VideoTrack recibido para sesion %s", session_id)
                asyncio.create_task(self._process_video_track(track, session_id))

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            logger.info("WebRTC estado de conexion [%s]: %s", session_id, pc.connectionState)
            if pc.connectionState in ["failed", "closed"]:
                await self.close_session(session_id)

        offer = RTCSessionDescription(sdp=sdp, type=sdp_type)
        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
        }

    async def handle_ice_candidate(self, session_id: str, candidate_data: dict[str, Any]) -> bool:
        pc = self.pcs.get(session_id)
        if not pc or not candidate_data:
            return False

        candidate_str = candidate_data.get("candidate")
        if not candidate_str:
            return True

        sdp_mid = candidate_data.get("sdpMid")
        sdp_mline_index = candidate_data.get("sdpMLineIndex")

        # Parse and add candidate if aiortc helper is available
        try:
            from aiortc.sdp import candidate_from_sdp
            cand = candidate_from_sdp(candidate_str)
            cand.sdpMid = sdp_mid
            cand.sdpMLineIndex = sdp_mline_index
            await pc.addIceCandidate(cand)
            return True
        except Exception as error:
            logger.warning("No se pudo agregar ICE candidate: %s", error)
            return False

    async def _process_video_track(self, track: Any, session_id: str) -> None:
        """Loop that continuously drains frames from the video track and passes the latest to YOLO."""
        is_analyzing = False

        while True:
            try:
                frame = await track.recv()
            except Exception:
                logger.info("Fin de transmision de video para sesion %s", session_id)
                break

            # If YOLO/Depth is still working on the previous frame, skip this one
            # to guarantee true zero-lag real-time execution.
            if is_analyzing:
                continue

            is_analyzing = True

            async def _analyze(current_frame: Any) -> None:
                nonlocal is_analyzing
                try:
                    # Convert aiortc VideoFrame to JPEG in memory
                    pil_image = current_frame.to_image()
                    buffer = BytesIO()
                    pil_image.save(buffer, format="JPEG", quality=68, optimize=False)
                    jpeg_bytes = buffer.getvalue()

                    # Run hybrid realtime pipeline in threadpool
                    result = await run_in_threadpool(realtime_analyze, jpeg_bytes, session_id=session_id)

                    # Send detection result via RTCDataChannel to phone
                    channels = self.data_channels.get(session_id, [])
                    if channels:
                        message = json.dumps(result)
                        for ch in list(channels):
                            if getattr(ch, "readyState", None) == "open":
                                ch.send(message)
                except Exception as err:
                    logger.error("Error procesando frame WebRTC [%s]: %s", session_id, err)
                finally:
                    is_analyzing = False

            asyncio.create_task(_analyze(frame))

    async def close_session(self, session_id: str) -> None:
        pc = self.pcs.pop(session_id, None)
        self.data_channels.pop(session_id, None)
        if pc:
            try:
                await pc.close()
            except Exception:
                pass

    async def close_all(self) -> None:
        sessions = list(self.pcs.keys())
        for session_id in sessions:
            await self.close_session(session_id)


webrtc_manager = WebRTCManager()

