// [FR30/FR31/FR54] One money formatter for every commercial screen — amounts
// travel as integer paise (never floats) and are shown in rupees with the
// member's own locale digits and separators.
// Traces to: FR30, FR31, FR54
export function formatPaise(paise: number, language: string): string {
  return new Intl.NumberFormat(`${language}-IN`, { style: "currency", currency: "INR" }).format(paise / 100);
}
