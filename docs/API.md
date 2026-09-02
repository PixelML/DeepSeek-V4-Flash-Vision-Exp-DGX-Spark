# API integration

The head node serves an OpenAI-compatible API. Keep it on a private network, or publish it through an authenticated TLS reverse proxy.

## List models

```bash
export DSV4_BASE_URL="https://your-proxy.example/v1"
export DSV4_API_KEY="replace-me"

curl -fsS \
  -H "Authorization: Bearer ${DSV4_API_KEY}" \
  "${DSV4_BASE_URL}/models"
```

## Text request

```bash
curl -fsS "${DSV4_BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${DSV4_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "deepseek-v4-flash-vision-exp",
    "messages": [{"role": "user", "content": "Reply with exactly one word: the color of a clear daytime sky."}],
    "temperature": 0,
    "max_tokens": 200
  }'
```

## Image request

The served model accepts an image as a `data:` URL alongside text in the same message. This example asks a one-word color question about a small inline PNG:

```bash
curl -fsS "${DSV4_BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${DSV4_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "deepseek-v4-flash-vision-exp",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What is the single dominant color in this image? Answer with exactly one color word."},
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAYklEQVR4nO3PMQ0AIADAMEAD/pUhBhEcDcmqYJt7n/GzpQNeNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaA1oDWgNaBdQgMBhJzbtzUAAAAASUVORK5CYII="}}
        ]
      }
    ],
    "temperature": 0,
    "max_tokens": 200
  }'
```

The model reports `multimodal_tokens` inside `usage.prompt_tokens_details` for image input, separate from plain text prompt tokens. Count both from the final `usage` object in the response, not from an intermediate streaming event.

## Notes

- Context is 1,048,576 tokens. Very long prompts (hundreds of thousands of tokens) can stall before the engine starts working; see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
- There is no video encoder in the official checkpoint. Sending a GIF is read as a single still frame.
- `reasoning` content streams alongside `content` for this model; read the final `usage` object rather than counting streamed chunks for token totals.
