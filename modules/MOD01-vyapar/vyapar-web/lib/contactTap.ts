// [FE2 — critique L4] Open the dialler or WhatsApp inside the tap itself.
// Waiting for the "record this attempt" request first meant that on a slow
// connection the tap seemed to do nothing, and the browser could treat a
// late window.open as a pop-up. The attempt is recorded right after, with
// fetch keepalive (see the SDK), without holding up the link.
export function openContactNow(channel: string, href: string): void {
  if (typeof window === "undefined") return;
  if (channel === "whatsapp") {
    window.open(href, "_blank", "noopener");
  } else {
    window.location.href = href;
  }
}
