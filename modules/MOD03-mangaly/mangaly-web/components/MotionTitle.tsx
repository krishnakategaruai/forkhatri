/* Motion typography for headlines (DEC-V1-030).
 *
 * Splits a heading into words; each word rises and settles from a wide cut
 * of the variable display face to its regular width (see `.mt__w` in
 * app/sindoor.css). Splitting by word rather than by letter keeps Hindi and
 * Telugu intact: their conjuncts and vowel signs must never be separated.
 * The full text stays in one accessible node, so a screen reader hears the
 * sentence, not a list of fragments. `accent` marks words (by index) drawn in
 * the kumkum-to-gold shimmer. */

type Props = {
  text: string;
  as?: "h1" | "h2" | "p";
  className?: string;
  accent?: number[];
};

export default function MotionTitle({ text, as: Tag = "h1", className, accent = [] }: Props) {
  const words = text.split(/(\s+)/).filter((w) => w.length > 0);
  let index = 0;
  return (
    <Tag className={className} aria-label={text}>
      <span className="mt" aria-hidden="true">
        {words.map((word, i) => {
          if (/^\s+$/.test(word)) return word;
          const n = index++;
          return (
            <span
              key={i}
              className={`mt__w${accent.includes(n) ? " mt--accent" : ""}`}
              style={{ "--i": n } as React.CSSProperties}
            >
              {word}
            </span>
          );
        })}
      </span>
    </Tag>
  );
}
