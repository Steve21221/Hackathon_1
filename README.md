# Promptly

Promptly is a starter website for sending user prompts to an external language model and displaying its response.

## Model API contract

The website sends `POST MODEL_API_URL` with JSON:

```json
{ "prompt": "The user's input" }
```

The model service can return any one of these string fields:

```json
{ "output": "The model response" }
```

`response` and `text` are also accepted. If the model requires a bearer token, set `MODEL_API_KEY`. Both values are server-only. Copy `.env.example` to `.env.local` when the model endpoint is ready. Without `MODEL_API_URL`, the app uses a demo response.

## Run it on your computer

1. Install [Node.js 22 or newer](https://nodejs.org/).
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Run:

```bash
npm install
npm run dev
```

5. Open the local address shown in the terminal, normally <http://localhost:3000>.

The website works in demo mode without a model. To connect a model running on the same computer, copy `.env.example` to `.env.local`, set `MODEL_API_URL` to the model server's local HTTP endpoint, and restart the website.

To check the production build, run:

```bash
npm run build
```

Before launch, confirm the model team's authentication method, request/response schema, rate limits, timeout expectations, and whether prompts may contain sensitive data.
