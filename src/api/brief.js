export const onRequestPost = async ({ request }) => {
  const { tickers } = Object.fromEntries(new URL(request.url).searchParams);
  const prompt = `Give a concise pre-market outlook (${new Date().toDateString()}) for tickers: ${tickers}.`;
  const body = JSON.stringify({
    model: "gpt-4o-mini",
    temperature: 0.3,
    max_tokens: 120,
    messages: [{ role: "user", content: prompt }],
  });

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.VITE_OPENAI_KEY}`,
      "Content-Type": "application/json",
    },
    body,
  });

  const data = await res.json();
  return new Response(data.choices?.[0]?.message?.content || "AI brief unavailable");
};
