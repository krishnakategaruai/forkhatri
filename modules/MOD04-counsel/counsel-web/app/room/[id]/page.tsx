"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Circle, PictureInPicture2, Settings2, ThumbsDown, ThumbsUp, WifiOff, Download, FileUp, Maximize2, Mic, MicOff, Minimize2, MonitorUp, Paperclip, Phone, PhoneOff, Send, Trash2, Video, VideoOff } from "lucide-react";
import { API_BASE, WS_BASE, api, type ActionItem, type Message, type RoomFile, type RoomState } from "@/lib/api";
import { dateLong, fileSize, timeShort } from "@/lib/format";
import { Avatar, Dialog, Skeleton, useToast } from "@/components/ui";

type Tab = "chat" | "notes" | "private" | "actions" | "files";

/* Two-party WebRTC over the service's own WebSocket for signalling.
 * The provider makes the offer (deterministic roles avoid glare). */
export default function RoomPage() {
  const { id } = useParams<{ id: string }>();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const toast = useToast();
  const [state, setState] = useState<RoomState | null>(null);
  const [tab, setTab] = useState<Tab>("chat");
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [shared, setShared] = useState("");
  const [priv, setPriv] = useState("");
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [files, setFiles] = useState<RoomFile[]>([]);
  const [newAction, setNewAction] = useState("");
  const [present, setPresent] = useState<string[]>([]);
  const [recording, setRecording] = useState(false);
  const [sharing, setSharing] = useState<string | null>(null);
  const [consents, setConsents] = useState<string[]>([]);
  const [mic, setMic] = useState(true);
  const [cam, setCam] = useState(true);
  const [joined, setJoined] = useState(false);
  const [remoteOn, setRemoteOn] = useState(false);
  const [typing, setTyping] = useState(false);
  // What each side is sending: a voice call sends no camera until someone turns it on.
  const [otherVideo, setOtherVideo] = useState(false);
  const [otherSpeaking, setOtherSpeaking] = useState(false);
  const [full, setFull] = useState(false);
  const [needsTap, setNeedsTap] = useState(false);
  // Pre-join preview (Meet / Zoom): see yourself and check the mic before joining.
  const [preview, setPreview] = useState<MediaStream | null>(null);
  const [level, setLevel] = useState(0);
  const previewVideo = useRef<HTMLVideoElement>(null);
  const [left, setLeft] = useState(false);
  const [unread, setUnread] = useState(0);
  const [net, setNet] = useState<"good" | "weak" | "reconnecting">("good");
  const [showControls, setShowControls] = useState(true);
  // Self-view corner (Meet: drag to any corner) and device pickers.
  const [corner, setCorner] = useState<"br" | "bl" | "tr" | "tl">("br");
  const drag = useRef<{ x: number; y: number } | null>(null);
  const [devOpen, setDevOpen] = useState(false);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [camId, setCamId] = useState("");
  const [micId, setMicId] = useState("");
  const [rated, setRated] = useState<null | "good" | "bad" | "sent">(null);
  const [issues, setIssues] = useState<string[]>([]);
  const tabRef = useRef<Tab>("chat");
  const callBox = useRef<HTMLDivElement>(null);

  const ws = useRef<WebSocket | null>(null);
  const pc = useRef<RTCPeerConnection | null>(null);
  const local = useRef<MediaStream | null>(null);
  const screen = useRef<MediaStream | null>(null);
  const localVideo = useRef<HTMLVideoElement>(null);
  const remoteVideo = useRef<HTMLVideoElement>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const noteTimer = useRef<number | null>(null);
  const privTimer = useRef<number | null>(null);
  const chatEnd = useRef<HTMLDivElement>(null);
  const stateRef = useRef<RoomState | null>(null);

  const load = useCallback(async () => {
    const s = await api<RoomState>(`/bookings/${id}/room`);
    setState(s); setShared(s.shared_note.body); setPriv(s.private_note.body); setActions(s.actions); setFiles(s.files);
    setConsents(s.consents); setRecording(s.recording); setPresent(s.present);
    setMsgs(await api<Message[]>(`/bookings/${id}/messages`));
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { const box = chatEnd.current?.parentElement; if (box) box.scrollTop = box.scrollHeight; }, [msgs.length, tab, typing]);

  const send = useCallback((payload: unknown) => { if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify(payload)); }, []);

  const ensurePeer = useCallback(() => {
    if (pc.current) return pc.current;
    const p = new RTCPeerConnection({ iceServers: stateRef.current?.ice_servers ?? [] });
    p.onicecandidate = (e) => { if (e.candidate) send({ type: "ice", candidate: e.candidate }); };
    // One remote stream collects every incoming track, including a camera that is
    // switched on later in a voice call (that track arrives without a stream).
    const remote = new MediaStream();
    p.ontrack = (e) => {
      if (!remote.getTracks().includes(e.track)) remote.addTrack(e.track);
      if (remoteVideo.current && remoteVideo.current.srcObject !== remote) remoteVideo.current.srcObject = remote;
      // Browsers may block sound until the person taps; offer a tap instead of silence.
      remoteVideo.current?.play().then(() => setNeedsTap(false)).catch(() => setNeedsTap(true));
      setRemoteOn(true);
    };
    p.onconnectionstatechange = () => {
      const st = p.connectionState;
      if (st === "connected") setNet("good");
      if (st === "disconnected") setNet("reconnecting");
      if (st === "failed") {
        setNet("reconnecting");
        // Recover without anyone pressing anything: the consultant redials.
        if (stateRef.current?.role === "provider" && pc.current === p) { p.close(); pc.current = null; void makeOfferRef.current?.(); }
        else send({ type: "ready" });
      }
      if (st === "closed") setRemoteOn(false);
    };
    local.current?.getTracks().forEach((tr) => p.addTrack(tr, local.current!));
    // Keep a video lane even on a voice call, so either side can turn the camera
    // (or screen share) on later without redialling.
    if (!local.current?.getVideoTracks().length) p.addTransceiver("video", { direction: "sendrecv" });
    pc.current = p;
    return p;
  }, [send]);

  const makeOfferRef = useRef<(() => Promise<void>) | null>(null);
  const makeOffer = useCallback(async () => {
    const p = ensurePeer();
    const offer = await p.createOffer();
    await p.setLocalDescription(offer);
    send({ type: "offer", sdp: offer });
  }, [ensurePeer, send]);

  // WebSocket: live updates always (chat, notes, actions), signalling once joined.
  useEffect(() => {
    if (!state) return;
    let sock: WebSocket | null = null;
    let closed = false;
    const ping = window.setInterval(() => send({ type: "ping" }), 25000);
    // A single-use ticket carries identity to the socket even when the session
    // cookie cannot travel (tunnelled development, different hostnames).
    void api<{ ticket: string }>("/me/ws-ticket", { method: "POST" }).then(({ ticket }) => {
      if (closed) return;
      sock = new WebSocket(`${WS_BASE}/ws/bookings/${id}?ticket=${encodeURIComponent(ticket)}`);
      ws.current = sock;
      sock.onmessage = onMessage;
      // A "ready" sent before the socket opened is lost; say it again on open.
      sock.onopen = () => { if (local.current) send({ type: "ready" }); };
    }).catch(() => toast(t("room.socket_failed")));
    const onMessage = async (ev: MessageEvent) => {
      const m = JSON.parse(ev.data);
      switch (m.type) {
        case "presence": {
          setPresent(m.present); setRecording(m.recording); setSharing(m.sharing);
          const other = m.present.find((x: string) => x !== stateRef.current?.me);
          if (!other) { setRemoteOn(false); setOtherVideo(false); pc.current?.close(); pc.current = null; }
          break;
        }
        // Handshake: whoever turns their camera on says "ready". The consultant
        // answers a "ready" by (re)starting the call; the person booking answers
        // the consultant's "ready" with their own. So the call starts whichever
        // side joins first, and never while the other has no camera yet.
        case "ready": {
          if (!local.current) return;
          send({ type: "media", video: hasLiveVideo() });
          if (stateRef.current?.role === "provider") { pc.current?.close(); pc.current = null; void makeOffer(); }
          else send({ type: "ready" });
          break;
        }
        case "offer": {
          if (!local.current) return;
          // Every offer starts a fresh call (the consultant resets before offering),
          // so a stale connection from before a reload or drop is never reused.
          pc.current?.close(); pc.current = null;
          const p = ensurePeer();
          await p.setRemoteDescription(m.sdp);
          // A voice-only answerer still opens its video lane for later.
          p.getTransceivers().forEach((tr) => { if (tr.direction === "recvonly") tr.direction = "sendrecv"; });
          const ans = await p.createAnswer();
          await p.setLocalDescription(ans);
          send({ type: "answer", sdp: ans });
          break;
        }
        case "answer": await pc.current?.setRemoteDescription(m.sdp); break;
        case "media": setOtherVideo(!!m.video); break;
        case "ice": try { await pc.current?.addIceCandidate(m.candidate); } catch { /* ignore */ } break;
        case "chat":
          setMsgs((s) => (s.some((x) => x.id === m.message.id) ? s : [...s, m.message])); setTyping(false);
          if (m.message.sender_id !== stateRef.current?.me && (tabRef.current !== "chat" || document.fullscreenElement)) {
            setUnread((u) => u + 1);
            toast(`${stateRef.current?.names[m.message.sender_id] ?? ""}: ${String(m.message.body).slice(0, 80)}`);
          }
          break;
        case "typing": setTyping(true); window.setTimeout(() => setTyping(false), 2500); break;
        case "note": if (m.by !== stateRef.current?.me) setShared(m.body); break;
        case "action": setActions((s) => (s.some((a) => a.id === m.action.id) ? s.map((a) => (a.id === m.action.id ? m.action : a)) : [...s, m.action])); break;
        case "action_removed": setActions((s) => s.filter((a) => a.id !== m.id)); break;
        case "file": setFiles((s) => (s.some((f) => f.id === m.file.id) ? s : [...s, m.file])); break;
        case "file_removed": setFiles((s) => s.filter((f) => f.id !== m.id)); break;
        case "consents": setConsents(m.consents); break;
        case "recording": setRecording(m.on); chime(m.on); toast(m.on ? t("room.recording_started") : t("room.recording_stopped")); break;
        case "sharing": setSharing(m.sharing); break;
        case "booking": void load(); break;
        case "error": if (m.code === "consent_required") toast(t("room.consent_required")); break;
      }
    };
    return () => { closed = true; window.clearInterval(ping); sock?.close(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, !!state]);

  const hasLiveVideo = () => !!screen.current || !!local.current?.getVideoTracks().some((tr) => tr.enabled && tr.readyState === "live");
  const videoSender = () => pc.current?.getTransceivers().find((tr) => tr.receiver.track.kind === "video")?.sender;

  const startPreview = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setPreview(s);
    } catch { toast(t("room.media_denied")); }
  };
  const stopPreview = () => { preview?.getTracks().forEach((tr) => tr.stop()); setPreview(null); };

  const join = async (withVideo: boolean) => {
    try {
      setLeft(false);
      if (preview) {
        // Reuse the checked devices; a voice join drops the camera.
        if (!withVideo) preview.getVideoTracks().forEach((tr) => { tr.stop(); preview.removeTrack(tr); });
        local.current = preview; setPreview(null);
      } else {
        // Voice: only the microphone is asked for; the camera is never touched.
        local.current = await navigator.mediaDevices.getUserMedia({ video: withVideo, audio: true });
      }
      if (localVideo.current) localVideo.current.srcObject = local.current;
      setCam(withVideo);
      setJoined(true);
      send({ type: "ready" });
      send({ type: "media", video: withVideo });
    } catch { toast(t(withVideo ? "room.media_denied" : "room.mic_denied")); }
  };

  const leave = () => {
    if (recorder.current) { stopRecorder(); send({ type: "recording", on: false }); }
    local.current?.getTracks().forEach((tr) => tr.stop()); screen.current?.getTracks().forEach((tr) => tr.stop());
    pc.current?.close(); pc.current = null; local.current = null; setJoined(false); setRemoteOn(false);
    if (document.fullscreenElement) void document.exitFullscreen().catch(() => {});
    setFull(false); setLeft(true); setNet("good");
  };

  const toggleMicRef = useRef<(() => void) | null>(null);
  const toggleCamRef = useRef<(() => Promise<void>) | null>(null);
  const toggleMic = () => { local.current?.getAudioTracks().forEach((tr) => (tr.enabled = !mic)); setMic(!mic); };
  const toggleCam = async () => {
    const camTrack = local.current?.getVideoTracks()[0];
    if (!camTrack) {
      // Voice call → video: ask for the camera now and send it on the existing lane.
      try {
        const v = await navigator.mediaDevices.getUserMedia({ video: true });
        const track = v.getVideoTracks()[0];
        local.current?.addTrack(track);
        if (!screen.current) await videoSender()?.replaceTrack(track);
        if (localVideo.current && local.current) localVideo.current.srcObject = local.current;
        setCam(true); send({ type: "media", video: true });
      } catch { toast(t("room.media_denied")); }
      return;
    }
    camTrack.enabled = !cam;
    setCam(!cam);
    send({ type: "media", video: !cam || !!screen.current });
  };

  const toggleShare = async () => {
    if (screen.current) {
      screen.current.getTracks().forEach((tr) => tr.stop()); screen.current = null;
      const camTrack = local.current?.getVideoTracks()[0] ?? null;
      await videoSender()?.replaceTrack(camTrack);
      if (localVideo.current && local.current) localVideo.current.srcObject = local.current;
      send({ type: "sharing", on: false });
      send({ type: "media", video: !!camTrack && cam });
      return;
    }
    try {
      const ds = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      screen.current = ds;
      const track = ds.getVideoTracks()[0];
      await videoSender()?.replaceTrack(track);
      if (localVideo.current) localVideo.current.srcObject = ds;
      track.onended = () => void toggleShare();
      send({ type: "sharing", on: true });
      send({ type: "media", video: true });
    } catch { /* cancelled */ }
  };

  // The person who presses record captures the call in their own browser (remote
  // video, both voices mixed) and uploads it to the workspace when it stops.
  const startRecorder = () => {
    const remote = remoteVideo.current?.srcObject as MediaStream | null;
    if (!remote && !local.current) return false;
    const ctx = new AudioContext();
    const dest = ctx.createMediaStreamDestination();
    for (const s of [remote, local.current]) if (s && s.getAudioTracks().length) ctx.createMediaStreamSource(s).connect(dest);
    const video = otherVideo ? remote?.getVideoTracks()[0] : hasLiveVideo() ? local.current?.getVideoTracks()[0] : undefined;
    const mixed = new MediaStream([...(video ? [video] : []), ...dest.stream.getAudioTracks()]);
    const kind = video ? "video/webm" : "audio/webm";
    const rec = new MediaRecorder(mixed, { mimeType: video && MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus") ? "video/webm;codecs=vp8,opus" : kind });
    chunks.current = [];
    rec.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
    rec.onstop = async () => {
      void ctx.close();
      const blob = new Blob(chunks.current, { type: kind });
      if (!blob.size) return;
      const form = new FormData(); form.append("file", new File([blob], "recording.webm", { type: kind }));
      try { await api(`/bookings/${id}/recordings`, { form }); toast(t("room.recording_saved")); } catch (e) { toast((e as Error).message); }
    };
    rec.start(5000);
    recorder.current = rec;
    return true;
  };
  const stopRecorder = () => { if (recorder.current && recorder.current.state !== "inactive") recorder.current.stop(); recorder.current = null; };

  // Mic level on the preview (the Zoom/Meet "is my mic working?" check).
  useEffect(() => {
    if (!preview) return;
    if (previewVideo.current) previewVideo.current.srcObject = preview;
    const ctx = new AudioContext();
    const an = ctx.createAnalyser(); an.fftSize = 512;
    ctx.createMediaStreamSource(preview).connect(an);
    const buf = new Uint8Array(an.frequencyBinCount);
    const h = window.setInterval(() => { an.getByteFrequencyData(buf); setLevel(Math.min(1, buf.reduce((a, b) => a + b, 0) / buf.length / 40)); }, 120);
    return () => { window.clearInterval(h); void ctx.close(); };
  }, [preview]);

  // Meet shortcuts: Ctrl/⌘+D mute, Ctrl/⌘+E camera.
  useEffect(() => {
    if (!joined) return;
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      const k = e.key.toLowerCase();
      if (k === "d") { e.preventDefault(); toggleMicRef.current?.(); }
      if (k === "e") { e.preventDefault(); void toggleCamRef.current?.(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [joined]);

  // Connection quality from WebRTC stats: round-trip time and packet loss.
  useEffect(() => {
    if (!remoteOn) return;
    let lastLost = 0, lastRecv = 0;
    const h = window.setInterval(async () => {
      const p = pc.current; if (!p || p.connectionState !== "connected") return;
      let rtt = 0, lost = 0, recv = 0;
      (await p.getStats()).forEach((r) => {
        if (r.type === "candidate-pair" && r.state === "succeeded" && r.currentRoundTripTime) rtt = r.currentRoundTripTime;
        if (r.type === "inbound-rtp") { lost += r.packetsLost ?? 0; recv += r.packetsReceived ?? 0; }
      });
      const dl = lost - lastLost, dr = recv - lastRecv; lastLost = lost; lastRecv = recv;
      const lossRate = dr + dl > 0 ? dl / (dr + dl) : 0;
      setNet((cur) => (cur === "reconnecting" ? cur : rtt > 0.6 || lossRate > 0.08 ? "weak" : "good"));
    }, 3000);
    return () => window.clearInterval(h);
  }, [remoteOn]);

  // Full screen on a phone: controls hide after a few seconds; tap to bring them back (Zoom mobile).
  useEffect(() => {
    if (!full || !showControls) return;
    const h = window.setTimeout(() => setShowControls(false), 4000);
    return () => window.clearTimeout(h);
  }, [full, showControls]);

  // Voice screen: a soft ring shows when the other person is speaking.
  useEffect(() => {
    if (!remoteOn || otherVideo) return;
    const stream = remoteVideo.current?.srcObject as MediaStream | null;
    if (!stream || !stream.getAudioTracks().length) return;
    const ctx = new AudioContext();
    const an = ctx.createAnalyser(); an.fftSize = 512;
    ctx.createMediaStreamSource(stream).connect(an);
    const buf = new Uint8Array(an.frequencyBinCount);
    const h = window.setInterval(() => { an.getByteFrequencyData(buf); setOtherSpeaking(buf.reduce((a, b) => a + b, 0) / buf.length > 12); }, 200);
    return () => { window.clearInterval(h); void ctx.close(); };
  }, [remoteOn, otherVideo]);

  // Full screen: the real browser full screen where supported, otherwise the
  // call fills the window (iPhone Safari only allows full screen on a bare video).
  useEffect(() => {
    const onChange = () => { if (!document.fullscreenElement) setFull(false); };
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);
  const toggleFull = async () => {
    if (full) {
      if (document.fullscreenElement) await document.exitFullscreen().catch(() => {});
      setFull(false);
      return;
    }
    setFull(true);
    try { await callBox.current?.requestFullscreen?.(); } catch { /* window-filling fallback stays on */ }
  };

  // Handlers read the latest values through refs; keep them current after each render.
  useEffect(() => {
    stateRef.current = state;
    tabRef.current = tab;
    makeOfferRef.current = makeOffer;
    toggleMicRef.current = toggleMic;
    toggleCamRef.current = toggleCam;
  });

  // Camera and mic pickers: list devices, and swap the live track without redialling.
  const openDevices = async () => {
    try { setDevices(await navigator.mediaDevices.enumerateDevices()); } catch { setDevices([]); }
    const cur = local.current;
    setCamId(cur?.getVideoTracks()[0]?.getSettings().deviceId ?? "");
    setMicId(cur?.getAudioTracks()[0]?.getSettings().deviceId ?? "");
    setDevOpen(true);
  };
  const switchDevice = async (kind: "video" | "audio", deviceId: string) => {
    try {
      const s = await navigator.mediaDevices.getUserMedia(kind === "video" ? { video: { deviceId: { exact: deviceId } } } : { audio: { deviceId: { exact: deviceId } } });
      const track = kind === "video" ? s.getVideoTracks()[0] : s.getAudioTracks()[0];
      const old = kind === "video" ? local.current?.getVideoTracks()[0] : local.current?.getAudioTracks()[0];
      if (old) { local.current?.removeTrack(old); old.stop(); }
      local.current?.addTrack(track);
      const sender = kind === "video" ? videoSender() : pc.current?.getTransceivers().find((tr) => tr.receiver.track.kind === "audio")?.sender;
      if (sender && !(kind === "video" && screen.current)) await sender.replaceTrack(track);
      if (kind === "audio") track.enabled = mic;
      if (localVideo.current && local.current && !screen.current) localVideo.current.srcObject = local.current;
      if (kind === "video") setCamId(deviceId); else setMicId(deviceId);
    } catch { toast(t("room.device_failed")); }
  };

  // Picture-in-picture (Meet): the other person floats over other apps and tabs.
  const pip = async () => {
    const v = remoteVideo.current;
    try {
      if (document.pictureInPictureElement) await document.exitPictureInPicture();
      else if (v && otherVideo) await v.requestPictureInPicture();
      else toast(t("room.pip_needs_video"));
    } catch { toast(t("room.pip_unsupported")); }
  };
  // Chrome can enter it automatically when the tab is switched during a call.
  useEffect(() => {
    if (!remoteOn || !otherVideo || !("mediaSession" in navigator)) return;
    try {
      navigator.mediaSession.setActionHandler("enterpictureinpicture" as MediaSessionAction, () => { void remoteVideo.current?.requestPictureInPicture().catch(() => {}); });
    } catch { /* not supported */ }
    return () => { try { navigator.mediaSession.setActionHandler("enterpictureinpicture" as MediaSessionAction, null); } catch { /* ignore */ } };
  }, [remoteOn, otherVideo]);

  // Drag the self-view; it snaps to the nearest corner.
  const onPipDown = (e: React.PointerEvent) => { drag.current = { x: e.clientX, y: e.clientY }; (e.target as HTMLElement).setPointerCapture?.(e.pointerId); };
  const onPipUp = (e: React.PointerEvent) => {
    if (!drag.current) return;
    const stage = (e.currentTarget as HTMLElement).parentElement?.getBoundingClientRect();
    drag.current = null;
    if (!stage) return;
    const right = e.clientX > stage.left + stage.width / 2, bottom = e.clientY > stage.top + stage.height / 2;
    setCorner(`${bottom ? "b" : "t"}${right ? "r" : "l"}` as "br" | "bl" | "tr" | "tl");
  };

  const sendFeedback = async (good: boolean, list: string[]) => {
    try { await api(`/bookings/${id}/call-feedback`, { body: { good, issues: list } }); setRated("sent"); } catch { setRated("sent"); }
  };

  // A short tone when recording starts or stops, as Zoom and Teams do.
  const chime = (on: boolean) => {
    try {
      const ctx = new AudioContext(); const o = ctx.createOscillator(); const g = ctx.createGain();
      o.frequency.value = on ? 880 : 520; g.gain.setValueAtTime(0.08, ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.35);
      o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + 0.36); o.onended = () => void ctx.close();
    } catch { /* no audio output */ }
  };

  const consent = async () => { const r = await api<{ consents: string[] }>(`/bookings/${id}/recording-consent`, { method: "POST" }); setConsents(r.consents); };
  const toggleRecording = () => {
    if (recording) { stopRecorder(); send({ type: "recording", on: false }); return; }
    if (startRecorder()) send({ type: "recording", on: true });
  };

  const sendChat = async () => {
    if (!text.trim()) return;
    const body = text.trim(); setText("");
    const m = await api<Message>(`/bookings/${id}/messages`, { body: { body } });
    setMsgs((s) => (s.some((x) => x.id === m.id) ? s : [...s, m]));
  };
  const onShared = (v: string) => {
    setShared(v);
    if (noteTimer.current) window.clearTimeout(noteTimer.current);
    noteTimer.current = window.setTimeout(() => void api(`/bookings/${id}/note`, { method: "PUT", body: { body: v, private: false } }), 600);
  };
  const onPriv = (v: string) => {
    setPriv(v);
    if (privTimer.current) window.clearTimeout(privTimer.current);
    privTimer.current = window.setTimeout(() => void api(`/bookings/${id}/note`, { method: "PUT", body: { body: v, private: true } }), 600);
  };
  const addAction = async () => {
    if (!newAction.trim()) return;
    const a = await api<ActionItem>(`/bookings/${id}/actions`, { body: { text: newAction.trim() } });
    setActions((s) => (s.some((x) => x.id === a.id) ? s : [...s, a])); setNewAction("");
  };
  const upload = async (f: File) => {
    const form = new FormData(); form.append("file", f);
    try { const r = await api<RoomFile>(`/bookings/${id}/files`, { form }); setFiles((s) => (s.some((x) => x.id === r.id) ? s : [...s, r])); toast(t("room.uploaded")); }
    catch (e) { toast((e as Error).message); }
  };

  if (!state) return <div className="wrap page"><Skeleton h={300} n={1} /></div>;
  const other = state.role === "seeker" ? state.booking.provider_id : state.booking.seeker_id;
  const otherName = state.names[other] ?? "";
  const otherHere = present.includes(other);
  const bothConsented = consents.includes(state.me) && consents.includes(other);
  const tabs: Tab[] = ["chat", "notes", "private", "actions", "files"];
  const voiceOnly = !state.booking.formats.includes("video");

  return (
    <div className="wrap room-shell">
      <div className="room-head" title={t("room.shortcuts")}>
        <Link href={`/bookings/${id}`} className="icon-btn" aria-label={t("room.back")}><ArrowLeft size={20} /></Link>
        <div style={{ minWidth: 0 }}>
          <div className="eyebrow hide-sm">{t("room.workspace")}</div>
          <div className="serif room-title">{state.booking.service_title} · <span className="muted">{otherName}</span></div>
          {state.live && (
            <div className="tiny row" style={{ gap: 6, color: otherHere ? "var(--ok)" : "var(--muted)" }}>
              <span className="presence" data-on={otherHere} />{otherHere ? t("room.other_here", { name: otherName }) : t("room.other_away", { name: otherName })}
            </div>
          )}
        </div>
      </div>

      <div className="room-layout">
        <div className="stack room-main" style={{ gap: 10 }}>
          <div ref={callBox} className={`call-box ${full ? "call-full" : ""}`}>
          <div className="room-stage" onClick={() => { if (full) setShowControls((v) => !v); }}>
            <video ref={remoteVideo} autoPlay playsInline style={{ display: remoteOn && otherVideo ? "block" : "none" }} />
            {remoteOn && !otherVideo && (
              <div className="voice-stage">
                <span className={`voice-ring ${otherSpeaking ? "on" : ""}`}><Avatar name={otherName} size={96} /></span>
                <div className="serif" style={{ fontSize: "1.3rem" }}>{otherName}</div>
                <div className="small" style={{ opacity: .75 }}>{t("room.on_voice")}</div>
              </div>
            )}
            {!remoteOn && preview && !joined && (
              <div className="preview">
                <video ref={previewVideo} autoPlay playsInline muted />
                <div className="preview-bar">
                  <span className="meter" aria-label={t("room.mic_level")}><span style={{ width: `${Math.round(level * 100)}%` }} /></span>
                  <span className="tiny">{level > 0.08 ? t("room.mic_ok") : t("room.mic_speak")}</span>
                </div>
                <div className="row preview-actions">
                  <button className="btn btn-primary" onClick={() => void join(true)}><Video size={16} />{t("room.join_now")}</button>
                  <button className="btn btn-on-dark" onClick={() => void join(false)}><Phone size={16} />{t("room.join_without_video")}</button>
                  <button className="btn btn-ghost" style={{ color: "#fff" }} onClick={stopPreview}>{t("common.cancel")}</button>
                </div>
              </div>
            )}
            {!remoteOn && !(preview && !joined) && (
              <div className="stage-empty stack" style={{ gap: 10 }}>
                {left ? (
                  <>
                    <p className="serif" style={{ fontSize: "1.3rem" }}>{t("room.you_left")}</p>
                    {rated === null && (
                      <div className="stack" style={{ gap: 8, justifyItems: "center" }}>
                        <span className="small">{t("room.how_was_call")}</span>
                        <div className="row" style={{ justifyContent: "center" }}>
                          <button className="btn btn-on-dark" onClick={() => void sendFeedback(true, [])} aria-label={t("room.call_good")}><ThumbsUp size={18} /></button>
                          <button className="btn btn-on-dark" onClick={() => setRated("bad")} aria-label={t("room.call_bad")}><ThumbsDown size={18} /></button>
                        </div>
                      </div>
                    )}
                    {rated === "bad" && (
                      <div className="stack" style={{ gap: 8, justifyItems: "center" }}>
                        <span className="small">{t("room.what_went_wrong")}</span>
                        <div className="row" style={{ justifyContent: "center" }}>
                          {["audio", "video", "screen", "connection", "echo", "other"].map((k) => (
                            <button key={k} className={`chip chip-dark ${issues.includes(k) ? "on" : ""}`} onClick={() => setIssues(issues.includes(k) ? issues.filter((x) => x !== k) : [...issues, k])}>{t(`room.issue.${k}`)}</button>
                          ))}
                        </div>
                        <button className="btn btn-primary btn-sm" onClick={() => void sendFeedback(false, issues)}>{t("common.send")}</button>
                      </div>
                    )}
                    {rated === "sent" && <p className="small">{t("room.thanks_feedback")}</p>}
                    <div className="row" style={{ justifyContent: "center" }}>
                      {state.live && <button className="btn btn-primary" onClick={() => setLeft(false)}>{t("room.rejoin")}</button>}
                      <Link href={`/bookings/${id}`} className="btn btn-on-dark">{t("room.back")}</Link>
                    </div>
                  </>
                ) : !state.live ? (state.booking.status === "confirmed" ? <p>{t("room.opens_at", { when: `${dateLong(new Date(new Date(state.booking.starts_at).getTime() - 15 * 60000).toISOString(), lang)}, ${timeShort(new Date(new Date(state.booking.starts_at).getTime() - 15 * 60000).toISOString(), lang)}` })}</p> : <p>{t("room.closed")}</p>) : !joined ? (
                  <>
                    <p className="serif" style={{ fontSize: "1.3rem" }}>{t("room.ready_title")}</p>
                    <p className="small">{voiceOnly ? t("room.ready_body_voice") : t("room.ready_body")}</p>
                    <div className="row" style={{ justifyContent: "center" }}>
                      {!voiceOnly && <button className="btn btn-primary btn-lg" onClick={() => void join(true)}><Video size={18} />{t("room.join")}</button>}
                      <button className={`btn btn-lg ${voiceOnly ? "btn-primary" : "btn-on-dark"}`} onClick={() => void join(false)}><Phone size={18} />{t("room.join_voice")}</button>
                    </div>
                    {!voiceOnly && <button className="link small" style={{ color: "#bfe9dd" }} onClick={() => void startPreview()}><Settings2 size={14} style={{ verticalAlign: "-2px" }} /> {t("room.check_first")}</button>}
                  </>
                ) : otherHere ? <p>{t("room.connecting")}</p> : <p>{t("room.waiting", { name: otherName })}</p>}
              </div>
            )}
            {needsTap && remoteOn && (
              <button className="btn btn-primary tap-sound" onClick={() => void remoteVideo.current?.play().then(() => setNeedsTap(false))}>{t("room.tap_sound")}</button>
            )}
            {recording && <div className="rec-banner" role="status">{t("room.rec_banner")}</div>}
            {recording && <span className="rec">{t("room.rec")}</span>}
            {joined && remoteOn && net !== "good" && (
              <div className="net-banner" role="status"><WifiOff size={14} />{net === "reconnecting" ? t("room.reconnecting") : t("room.weak")}
                {net === "weak" && cam && <button className="link" style={{ color: "#fff", marginLeft: 8 }} onClick={() => void toggleCam()}>{t("room.switch_voice")}</button>}
              </div>
            )}
            {remoteOn && otherVideo && <span className="stage-name">{sharing === other ? t("room.sharing_screen", { name: otherName }) : otherName}</span>}
            <div className={`pip pip-${corner}`} style={{ display: joined && (cam || sharing === state.me) ? "block" : "none" }} onPointerDown={onPipDown} onPointerUp={onPipUp} onClick={(e) => e.stopPropagation()} title={t("room.drag_self")}><video ref={localVideo} autoPlay playsInline muted /></div>
            {joined && (
              <div className="stage-tools" onClick={(e) => e.stopPropagation()}>
                <button className="stage-btn" onClick={() => void openDevices()} aria-label={t("room.devices")}><Settings2 size={17} /></button>
                {otherVideo && remoteOn && <button className="stage-btn" onClick={() => void pip()} aria-label={t("room.pip")}><PictureInPicture2 size={17} /></button>}
                <button className="stage-btn" onClick={() => void toggleFull()} aria-label={full ? t("room.exit_full") : t("room.full")}>{full ? <Minimize2 size={17} /> : <Maximize2 size={17} />}</button>
              </div>
            )}
          </div>
          {joined && (
            <div className={`controls ${full && !showControls ? "controls-hidden" : ""}`}>
              <button className={`ctl ${mic ? "" : "off"}`} onClick={toggleMic} aria-label={mic ? t("room.mute") : t("room.unmute")}>{mic ? <Mic /> : <MicOff />}</button>
              <button className={`ctl ${cam ? "" : "off"}`} onClick={() => void toggleCam()} aria-label={cam ? t("room.cam_off") : t("room.cam_on")}>{cam ? <Video /> : <VideoOff />}</button>
              <button className={`ctl ${sharing === state.me ? "on" : ""}`} onClick={() => void toggleShare()} aria-label={t("room.share")}><MonitorUp /></button>
              {state.booking.recording_allowed && (
                bothConsented ? (
                  <button className={`ctl ${recording ? "on" : ""}`} onClick={toggleRecording} aria-label={t("room.record")}><Circle fill={recording ? "currentColor" : "none"} /></button>
                ) : (
                  <button className="btn btn-secondary btn-sm" onClick={() => void consent()} disabled={consents.includes(state.me)}>{consents.includes(state.me) ? t("room.consent_waiting") : t("room.consent")}</button>
                )
              )}
              <button className="ctl end" onClick={leave} aria-label={t("room.leave")}><PhoneOff /></button>
            </div>
          )}
          </div>
          {state.booking.brief && <div className="card card-pad small room-brief" style={{ color: "var(--ink-2)" }}><span className="eyebrow">{state.role === "provider" ? t("booking.brief_provider") : t("booking.brief")}</span><p style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>{state.booking.brief}</p></div>}
        </div>

        <div className="card room-side">
          <div className="room-tabs" role="tablist">
            {tabs.map((k) => <button key={k} role="tab" aria-selected={tab === k} onClick={() => { setTab(k); if (k === "chat") setUnread(0); }}>{t(`room.tab.${k}`)}{k === "chat" && unread > 0 && <span className="badge">{unread}</span>}</button>)}
          </div>
          <div className={`room-panel stack ${tab === "chat" ? "chat" : ""}`} style={{ gap: 8 }}>
            {tab === "chat" && (
              <>
                <div className="stack chat-scroll" style={{ gap: 8 }}>
                  {msgs.map((m) => m.kind === "system" ? <div key={m.id} className="bubble sys">{t(`system.${m.body}`, { defaultValue: m.body })}</div> : (
                    <div key={m.id} className={`bubble ${m.sender_id === state.me ? "mine" : ""}`}>{m.kind === "file" ? `📎 ${m.body}` : m.body}<div className="tiny muted">{timeShort(m.created_at, lang)}</div></div>
                  ))}
                  {typing && <div className="tiny muted">{t("room.typing", { name: otherName })}</div>}
                  <div ref={chatEnd} />
                </div>
                <form className="row chat-form" style={{ flexWrap: "nowrap", gap: 6 }} onSubmit={(e) => { e.preventDefault(); void sendChat(); }}>
                  <input className="input" value={text} onChange={(e) => { setText(e.target.value); send({ type: "typing" }); }} placeholder={t("booking.message_placeholder")} />
                  <button className="btn btn-primary" type="submit" aria-label={t("common.send")}><Send size={16} /></button>
                </form>
              </>
            )}
            {tab === "notes" && (<><p className="tiny muted">{t("room.notes_hint")}</p><textarea className="notepad" value={shared} onChange={(e) => onShared(e.target.value)} placeholder={t("room.notes_placeholder")} /></>)}
            {tab === "private" && (<><p className="tiny muted">{t("room.private_hint")}</p><textarea className="notepad" value={priv} onChange={(e) => onPriv(e.target.value)} placeholder={t("room.private_placeholder")} /></>)}
            {tab === "actions" && (
              <>
                <form className="row" style={{ flexWrap: "nowrap", gap: 6 }} onSubmit={(e) => { e.preventDefault(); void addAction(); }}>
                  <input className="input" value={newAction} onChange={(e) => setNewAction(e.target.value)} placeholder={t("room.action_placeholder")} />
                  <button className="btn btn-primary btn-sm" type="submit">{t("common.add")}</button>
                </form>
                <div className="list">
                  {actions.map((a) => (
                    <label key={a.id} className="item check" style={{ padding: "8px 0" }}>
                      <input type="checkbox" checked={a.done} onChange={(e) => void api(`/bookings/${id}/actions/${a.id}`, { method: "PATCH", body: { done: e.target.checked } })} />
                      <span className="grow small" style={{ textDecoration: a.done ? "line-through" : undefined }}>{a.text}</span>
                      <button className="icon-btn" aria-label={t("common.remove")} onClick={(e) => { e.preventDefault(); void api(`/bookings/${id}/actions/${a.id}`, { method: "DELETE" }); }}><Trash2 size={15} /></button>
                    </label>
                  ))}
                  {!actions.length && <p className="tiny muted">{t("room.no_actions")}</p>}
                </div>
              </>
            )}
            {tab === "files" && (
              <>
                <label className="btn btn-secondary btn-sm" style={{ justifySelf: "start" }}><FileUp size={15} />{t("room.upload")}<input type="file" className="sr" onChange={(e) => { const f = e.target.files?.[0]; if (f) void upload(f); e.target.value = ""; }} /></label>
                <div className="list">
                  {files.map((f) => (
                    <div key={f.id} className="item" style={{ padding: "8px 0" }}>
                      <Paperclip size={15} className="muted" />
                      <div className="grow"><div className="small">{f.is_recording && <span className="tag tag-danger" style={{ marginRight: 6 }}>{t("room.rec")}</span>}{f.name}</div><div className="tiny muted">{fileSize(f.size_bytes)} · {state.names[f.owner_id]}</div></div>
                      <a className="icon-btn" href={`${API_BASE}/bookings/${id}/files/${f.id}`} target="_blank" rel="noopener noreferrer" aria-label={t("room.download")}><Download size={15} /></a>
                      {f.owner_id === state.me && <button className="icon-btn" aria-label={t("common.remove")} onClick={() => void api(`/bookings/${id}/files/${f.id}`, { method: "DELETE" })}><Trash2 size={15} /></button>}
                    </div>
                  ))}
                  {!files.length && <p className="tiny muted">{t("room.no_files")}</p>}
                </div>
                <p className="tiny muted">{t("room.files_note")}</p>
              </>
            )}
          </div>
        </div>
      </div>
      <Dialog open={devOpen} onClose={() => setDevOpen(false)} title={t("room.devices")}>
        <label className="field"><span className="label">{t("room.camera")}</span>
          <select className="select" value={camId} onChange={(e) => void switchDevice("video", e.target.value)} disabled={!camId}>
            {devices.filter((d) => d.kind === "videoinput").map((d, i) => <option key={d.deviceId || i} value={d.deviceId}>{d.label || `${t("room.camera")} ${i + 1}`}</option>)}
          </select></label>
        <label className="field"><span className="label">{t("room.microphone")}</span>
          <select className="select" value={micId} onChange={(e) => void switchDevice("audio", e.target.value)}>
            {devices.filter((d) => d.kind === "audioinput").map((d, i) => <option key={d.deviceId || i} value={d.deviceId}>{d.label || `${t("room.microphone")} ${i + 1}`}</option>)}
          </select></label>
        <div className="row" style={{ justifyContent: "flex-end" }}><button className="btn btn-primary" onClick={() => setDevOpen(false)}>{t("room.done")}</button></div>
      </Dialog>
    </div>
  );
}
