import React, { useEffect, useRef, useState } from "react";
import { createChart, CrosshairMode } from "lightweight-charts";

// --- ENV NOTE --------------------------------------------------------------
// Store your keys in environment variables and inject them at build time.
// vite.config.js example:
//  import { defineConfig } from 'vite';
//  export default defineConfig({
//    define: {
//      'process.env': {},
//      __FINNHUB__: JSON.stringify(process.env.VITE_FINNHUB_KEY),
//      __OPENAI__: JSON.stringify(process.env.VITE_OPENAI_KEY),
//    },
//  });
// ---------------------------------------------------------------------------

const SOCKET_BASE = `wss://ws.finnhub.io?token=${__FINNHUB__}`;

export default function App() {
  const chartEl = useRef(null);
  const candleSeries = useRef(null);

  const [ticker, setTicker] = useState("NVDA");
  const [positions, setPositions] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("positions") || "{}");
    } catch {
      return {};
    }
  });
  const [dailyBrief, setDailyBrief] = useState("Loading AI brief…");
  const [news, setNews] = useState([]);

  /* ---------- CHART INIT ------------------------------------------------- */
  useEffect(() => {
    if (!chartEl.current) return;
    const chart = createChart(chartEl.current, {
      width: chartEl.current.clientWidth,
      height: 380,
      crosshair: { mode: CrosshairMode.Normal },
      layout: {
        background: { type: "solid", color: "#0d1117" },
        textColor: "#e6edf3",
      },
      grid: {
        vertLines: { color: "#21262d" },
        horzLines: { color: "#21262d" },
      },
    });
    candleSeries.current = chart.addCandlestickSeries({
      upColor: "#16c784",
      downColor: "#ea3943",
      borderVisible: false,
      wickUpColor: "#16c784",
      wickDownColor: "#ea3943",
    });
    // Resize handler
    const handleResize = () => chart.resize(chartEl.current.clientWidth, 380);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  /* ---------- REAL‑TIME DATA -------------------------------------------- */
  useEffect(() => {
    if (!candleSeries.current) return;
    const ws = new WebSocket(SOCKET_BASE);

    // Minimal 1‑min aggregator
    let lastCandle = null;

    const flush = () => {
      if (!lastCandle) return;
      candleSeries.current.update(lastCandle);
    };

    ws.onopen = () => ws.send(JSON.stringify({ type: "subscribe", symbol: ticker }));
    ws.onmessage = (msg) => {
      const parsed = JSON.parse(msg.data);
      if (parsed.data) {
        parsed.data.forEach((tick) => {
          const t = Math.floor(tick.t / 60000) * 60; // bucket to minute
          if (!lastCandle || lastCandle.time !== t) {
            flush();
            lastCandle = { time: t, open: tick.p, high: tick.p, low: tick.p, close: tick.p };
          } else {
            lastCandle.high = Math.max(lastCandle.high, tick.p);
            lastCandle.low = Math.min(lastCandle.low, tick.p);
            lastCandle.close = tick.p;
          }
        });
      }
    };
    const interval = setInterval(flush, 5000);
    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [ticker]);

  /* ---------- AI DAILY BRIEF -------------------------------------------- */
  useEffect(() => {
    // This endpoint should run server‑side to keep your OpenAI key secret
    fetch(`/api/brief?tickers=${Object.keys(positions).join()}`)
      .then((r) => r.text())
      .then(setDailyBrief)
      .catch(() => setDailyBrief("Cannot fetch AI brief"));
  }, [positions]);

  /* ---------- NEWS + SENTIMENT ------------------------------------------ */
  useEffect(() => {
    fetch(`https://finnhub.io/api/v1/news/${ticker}?token=${__FINNHUB__}`)
      .then((r) => r.json())
      .then((articles) => setNews(articles.slice(0, 20)))
      .catch(console.error);
  }, [ticker]);

  /* ---------- POSITION FORM --------------------------------------------- */
  const addPosition = (sym, qty, price) => {
    setPositions((prev) => {
      const updated = { ...prev, [sym]: [...(prev[sym] || []), { qty, price }] };
      localStorage.setItem("positions", JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-gray-200 p-5 space-y-6 font-sans">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">Pre‑Market Dashboard</h1>
        <p className="bg-[#161b22] p-3 rounded-xl text-sm whitespace-pre-wrap">
          {dailyBrief}
        </p>
      </header>
      <section className="space-y-4">
        <div className="flex items-center space-x-2">
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            className="bg-[#161b22] rounded px-2 py-1 w-24"
          />
          <span className="text-xs text-gray-400">type a ticker & press enter</span>
        </div>
        <div ref={chartEl} />
      </section>
      <PositionForm onAdd={addPosition} />
      <NewsFeed news={news} />
    </div>
  );
}

/* ------------------ helper components ---------------------------------- */
function PositionForm({ onAdd }) {
  const [sym, setSym] = useState("NVDA");
  const [qty, setQty] = useState(0);
  const [price, setPrice] = useState(0);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onAdd(sym.toUpperCase(), Number(qty), Number(price));
      }}
      className="bg-[#161b22] p-4 rounded-xl flex flex-wrap gap-2 text-sm"
    >
      <input
        placeholder="Ticker"
        value={sym}
        onChange={(e) => setSym(e.target.value)}
        className="bg-[#0d1117] rounded px-2 py-1 w-20"
      />
      <input
        placeholder="Qty"
        type="number"
        value={qty}
        onChange={(e) => setQty(e.target.value)}
        className="bg-[#0d1117] rounded px-2 py-1 w-20"
      />
      <input
        placeholder="Fill $"
        type="number"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
        className="bg-[#0d1117] rounded px-2 py-1 w-24"
      />
      <button type="submit" className="bg-emerald-600 px-3 py-1 rounded text-white">
        Add Lot
      </button>
    </form>
  );
}

function NewsFeed({ news }) {
  if (!news.length) return null;
  return (
    <div className="space-y-2">
      <h2 className="font-semibold text-lg">Latest Headlines</h2>
      <ul className="divide-y divide-[#21262d]">
        {news.map((n) => (
          <li key={n.id} className="py-2 flex items-start gap-2">
            <span
              className={`h-3 w-3 rounded-full mt-1 ${n.sentiment === "Bearish" ? "bg-red-500" : "bg-green-500"}`}
            />
            <a href={n.url} target="_blank" rel="noreferrer" className="hover:underline">
              {n.headline}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
