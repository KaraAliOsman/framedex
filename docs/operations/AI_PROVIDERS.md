# AI providers

The gateway (`ai_routes`) binds each capability to `{provider, provider_model}`.
Routes are platform config — tenants only ever see `public_name`. `MOCK` is the
deterministic default and performs no network I/O.

## Transports

| Route `provider` | Transport | Wire |
| --- | --- | --- |
| `MOCK` | `MockProvider` | none — deterministic output |
| `MIMO`, `OPENAI`, `OPENROUTER`, `DEEPSEEK`, `QWEN` | `OpenAICompatibleProvider` | `POST {base}/chat/completions` |
| anything else | `HttpProvider` | `POST {base}/invoke` generic JSON |

`AI_GATEWAY_{P}_PROTOCOL=openai|http` overrides the registry either way.

## Env contract (per provider name)

```text
AI_GATEWAY_{P}_API_KEY    bearer token (required)
AI_GATEWAY_{P}_BASE_URL   https endpoint; e.g. https://api.ximimio…/v1
AI_GATEWAY_{P}_MODEL      optional — overrides the route's provider_model
AI_GATEWAY_{P}_PROTOCOL   optional — openai | http
```

The OpenAI transport reads two control keys from `input_payload`: `system`
(system prompt text) and `json_output` (requests `response_format` JSON mode).
Everything else is serialized as the user message.

## Activate MiMo for design_assist

1. Set `AI_GATEWAY_MIMO_API_KEY`, `AI_GATEWAY_MIMO_BASE_URL`
   (e.g. `https://api.ximimio.com/v1`), `AI_GATEWAY_MIMO_MODEL`.
2. Point the capability route at the provider — a privileged operational
   statement (routes are backend-read-only):

   ```sql
   UPDATE public.ai_routes
      SET provider = 'MIMO',
          provider_model = 'mimo-v1-pro',   -- informational; env model wins
          prompt_version = 'design-assist-v2'
    WHERE capability = 'design_assist';
   ```

3. Revert any time by restoring `provider = 'MOCK'`.

Every invocation still flows through the gateway's reconcile → entitlement +
balance check → sealed audit → wallet debit; a provider misconfiguration fails
closed (`ai_provider_unavailable`) before any debit.
