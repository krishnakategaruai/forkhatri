/**
 * The first-load splash (components/Splash.tsx) shows once per browser session.
 * SPLASH_BOOT_SCRIPT runs inline in <head> before first paint: on a repeat visit in
 * the same tab it marks <html data-splash="seen">, and CSS hides the server-rendered
 * splash, so a reload never flashes it. Kept out of the client component so the
 * server layout imports a plain string, not a client reference.
 */
export const SPLASH_SEEN_KEY = "fk.splash.v1";

export const SPLASH_BOOT_SCRIPT = `(function(){try{if(sessionStorage.getItem("${SPLASH_SEEN_KEY}"))document.documentElement.setAttribute("data-splash","seen")}catch(e){}})();`;

/** Transparent cut-out of Bhagwan Kartavirya Sahasrarjun; preloaded from the layout <head>. */
export const SPLASH_IMAGE = {
  src: "/assets/devotional/ssk-sahasrarjun.webp",
  width: 480,
  height: 737,
} as const;
