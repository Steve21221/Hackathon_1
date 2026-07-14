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

## Local development

Use Node 22 or newer, install dependencies, and run the development script. The production build is created with the build script.

Before launch, confirm the model team's authentication method, request/response schema, rate limits, timeout expectations, and whether prompts may contain sensitive data.
