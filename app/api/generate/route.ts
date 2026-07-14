import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { prompt?: unknown };
    const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
    if (!prompt) return NextResponse.json({ error: "Please enter a prompt." }, { status: 400 });
    if (prompt.length > 4000) return NextResponse.json({ error: "Prompt must be 4,000 characters or fewer." }, { status: 400 });

    const modelUrl = process.env.MODEL_API_URL;
    if (!modelUrl) {
      await new Promise((resolve) => setTimeout(resolve, 650));
      return NextResponse.json({
        output: `This is a demo response for: “${prompt}”\n\nYour website is working. When the model team provides an API URL, add it as MODEL_API_URL and this page will forward prompts to their service.`,
      });
    }

    const modelResponse = await fetch(modelUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(process.env.MODEL_API_KEY ? { Authorization: `Bearer ${process.env.MODEL_API_KEY}` } : {}),
      },
      body: JSON.stringify({ prompt }),
      signal: AbortSignal.timeout(60_000),
    });

    if (!modelResponse.ok) throw new Error(`Model service returned ${modelResponse.status}`);
    const modelData = (await modelResponse.json()) as { output?: unknown; response?: unknown; text?: unknown };
    const output = [modelData.output, modelData.response, modelData.text].find((value) => typeof value === "string");
    if (typeof output !== "string") throw new Error("Model response did not include output text.");
    return NextResponse.json({ output });
  } catch (error) {
    console.error("Model request failed", error);
    return NextResponse.json({ error: "We couldn't reach the model. Please try again." }, { status: 502 });
  }
}
