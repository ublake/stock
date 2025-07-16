export function calcLimit(priceHistory, pct = 3) {
  const lastClose = priceHistory.at(-1).close;
  return lastClose * (1 - pct / 100);          // simple % draw‑down
}
