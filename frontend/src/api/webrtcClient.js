import { getApiBaseUrl } from "./sensusClient";

/**
 * Cliente WebRTC para transmision continua de video en tiempo real.
 * Requiere 'react-native-webrtc'.
 */
export class SensusWebRTCClient {
  constructor({ onDetection, onStatusChange, onError }) {
    this.onDetection = onDetection || (() => {});
    this.onStatusChange = onStatusChange || (() => {});
    this.onError = onError || (() => {});
    this.pc = null;
    this.stream = null;
    this.dataChannel = null;
    this.isRunning = false;
  }

  async start({ facingMode = "environment" } = {}) {
    if (this.isRunning) return;

    let webrtc;
    try {
      webrtc = require("react-native-webrtc");
    } catch (err) {
      const msg = "react-native-webrtc no esta instalado en el APK.";
      this.onError(new Error(msg));
      throw new Error(msg);
    }

    const { RTCPeerConnection, mediaDevices } = webrtc;

    try {
      this.onStatusChange("Iniciando camara continua");

      // 1. Obtener stream continuo de camara
      this.stream = await mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode,
          frameRate: { ideal: 24, max: 30 },
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
      });

      this.onStatusChange("Negociando WebRTC");

      // 2. Crear conexion Peer
      const config = {
        iceServers: [
          { urls: "stun:stun.l.google.com:19302" },
          { urls: "stun:stun1.l.google.com:19302" },
        ],
      };
      this.pc = new RTCPeerConnection(config);

      // 3. Crear DataChannel para recibir alertas y detecciones de IA
      this.dataChannel = this.pc.createDataChannel("sensus-alerts", {
        ordered: true,
      });

      this.dataChannel.onopen = () => {
        this.onStatusChange("Video continuo activo");
      };

      this.dataChannel.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onDetection(data);
        } catch (e) {
          console.warn("[WebRTC] Error al parsear mensaje de IA:", e);
        }
      };

      this.pc.onconnectionstatechange = () => {
        const state = this.pc?.connectionState;
        if (state === "connected") {
          this.onStatusChange("Streaming activo");
        } else if (state === "disconnected" || state === "failed") {
          this.onStatusChange("Conexion interrumpida");
        }
      };

      // 4. Agregar el track de video al PeerConnection
      const videoTracks = this.stream.getVideoTracks();
      if (videoTracks.length === 0) {
        throw new Error("No se encontro un track de video en la camara.");
      }
      this.stream.getTracks().forEach((track) => {
        this.pc.addTrack(track, this.stream);
      });

      // 5. Crear oferta SDP
      const offer = await this.pc.createOffer();
      await this.pc.setLocalDescription(offer);

      // Esperar brevemente para agrupar ICE candidates en el SDP inicial
      await this._waitForIceCandidates();

      // 6. Enviar oferta al backend FastAPI
      const baseUrl = getApiBaseUrl();
      const sessionId = `mobile-${Date.now()}`;

      const res = await fetch(`${baseUrl}/api/webrtc/offer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sdp: this.pc.localDescription.sdp,
          type: this.pc.localDescription.type,
          session_id: sessionId,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Error en señalizacion WebRTC (${res.status}): ${text}`);
      }

      const answer = await res.json();
      await this.pc.setRemoteDescription(answer);

      this.isRunning = true;
      this.onStatusChange("Streaming continuo listo");
    } catch (err) {
      this.stop();
      this.onError(err);
      throw err;
    }
  }

  _waitForIceCandidates() {
    return new Promise((resolve) => {
      if (!this.pc || this.pc.iceGatheringState === "complete") {
        resolve();
        return;
      }

      const check = () => {
        if (!this.pc || this.pc.iceGatheringState === "complete") {
          if (this.pc) this.pc.removeEventListener("icegatheringstatechange", check);
          resolve();
        }
      };

      this.pc.addEventListener("icegatheringstatechange", check);
      // Timeout seguro de 1.2 segundos para no demorar la apertura
      setTimeout(() => {
        if (this.pc) this.pc.removeEventListener("icegatheringstatechange", check);
        resolve();
      }, 1200);
    });
  }

  stop() {
    this.isRunning = false;
    if (this.dataChannel) {
      try {
        this.dataChannel.close();
      } catch (e) {}
      this.dataChannel = null;
    }
    if (this.pc) {
      try {
        this.pc.close();
      } catch (e) {}
      this.pc = null;
    }
    if (this.stream) {
      try {
        this.stream.getTracks().forEach((track) => track.stop());
      } catch (e) {}
      this.stream = null;
    }
    this.onStatusChange("Video continuo detenido");
  }
}

