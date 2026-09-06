# Credit-safe Byte Voice v1 workflow

## Status

Implemented. The selected ElevenLabs voice is now treated as the frozen `byte_voice_v1`
identity for local development.

## TTS execution policy

`TTS_MODE=live` performs the normal fingerprint lookup first. A valid matching artifact is
always reused; ElevenLabs is called only after a cache miss. `TTS_MODE=cached` is the safe local
development mode: a cache hit proceeds, while a miss or invalid file raises an actionable error
without calling any TTS provider.

`Settings.local()` defaults to `cached` when no environment override is present. The safe
`.env.example` keeps the offline fake provider in `live` mode for compatibility. Directly constructed
settings retain `live` as a compatibility default for existing offline tests and injected fake
providers. The mode is deliberately excluded from the TTS fingerprint so switching between
live and cached does not invalidate narration.

## Cache integrity and observability

An audio artifact is reusable only when its database metadata fingerprint matches, its file
exists, its SHA-256 matches the stored artifact, and `AudioProbe` can read it. Live mode may
regenerate an invalid artifact; cached mode stops with `CachedNarrationError`.

The audio `StepRun` records `tts_provider`, `tts_mode`, `tts_cache_status`, `tts_fingerprint`,
`voice_version`, `model_id`, and `external_request_made`. Provider metadata continues to store
only response data actually returned by ElevenLabs, such as request ID, character count,
character cost, and request duration.

## Byte Voice v1 references

The CLI provides a controlled path for exactly two explicit reference texts:

```powershell
$env:TTS_PROVIDER = "elevenlabs"
$env:TTS_MODE = "live"
uv run --extra elevenlabs svg-run-manual --byte-voice-stress-test
```

The references use stable keys `byte-voice-v1-en-reference` and `byte-voice-v1-es-reference`,
so successful outputs are persisted through the normal artifact and StepRun repositories and
are reused on later runs. After generating a new reference, return to `TTS_MODE=cached` before
visual or rendering work.

## Speech/display boundary

`ScriptScene` now supports optional `display_text` and `speech_text` fields. Both default to
the existing narration, so captions continue to represent human-readable text while TTS can
diverge in a future pronunciation-normalization slice. No phonetic rewrites or pronunciation
dictionary are implemented. If the fields later differ materially, alignment reconciliation
will need an explicit policy.

## Scope and limitations

- No new voice design, cloning, remote voice changes, SFX, music, STT, or automatic phonetic
  rewriting is included.
- The stress-test command intentionally does not run visuals or render video.
- `byte_voice_v1` is a logical project identity; the account voice ID remains environment
  configuration and no secret is committed.
