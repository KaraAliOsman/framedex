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
AI_GATEWAY_{P}_BASE_URL   https endpoint; e.g. https://api.xiaomimimo…/v1
AI_GATEWAY_{P}_MODEL      optional — overrides the route's provider_model
AI_GATEWAY_{P}_PROTOCOL   optional — openai | http
AI_GATEWAY_{P}_TIMEOUT_S  optional — whole-request bound in s (default 60, 1-600)
```

`AI_GATEWAY_MOCK_ENABLED` gates the deterministic provider: `1` opts in
explicitly, `0` forces it off. Unset, MOCK serves only development (`DEBUG=1`)
and the test suite — a production stack with MOCK routes refuses
`ai_provider_mock_disabled` instead of answering with fabricated content.

The OpenAI transport takes two control options from the *server-owned*
`provider_options` channel (callers can never set them): `system` (system
prompt) and `json_output` (requests `response_format` JSON mode). Everything
in `input_payload` is serialized as the user message.

## Activate MiMo for design_assist

1. Set `AI_GATEWAY_MIMO_API_KEY`, `AI_GATEWAY_MIMO_BASE_URL`
   (pay-as-you-go `sk-` keys use `https://api.xiaomimimo.com/v1`;
   Token Plan `tp-` keys use the dedicated base URL shown on the plan
   page, e.g. `https://token-plan-cn.xiaomimimo.com/v1`),
   `AI_GATEWAY_MIMO_MODEL`.
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
