# ElevenLabs narration provider

## Status

Implemented as an optional local development provider. Automated tests remain offline.

## Delivered behavior

- Added `ElevenLabsTextToSpeechProvider` behind the existing `TextToSpeechProvider` port.
- Added explicit `TTS_PROVIDER=elevenlabs` selection; missing credentials fail clearly and do
  not fall back to another provider.
- Generates MP3 audio through the official `elevenlabs` Python SDK and preserves the existing
  ffprobe, caption alignment, timeline, and FFmpeg path.
- Stores request ID, character count, character cost when returned, model, voice, version, and
  output format as provider metadata without exposing credentials.
- Retries only transient 429 and 5xx responses, with two bounded exponential-backoff retries.

## Configuration

Install the optional dependency with `uv sync --extra elevenlabs`, then configure:

```dotenv
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_VOICE_VERSION=byte_voice_dev_v1
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_STABILITY=0.5
ELEVENLABS_SIMILARITY_BOOST=0.75
ELEVENLABS_STYLE=0.0
ELEVENLABS_USE_SPEAKER_BOOST=true
ELEVENLABS_SPEED=1.0
```

`eleven_multilingual_v2` is the default because ElevenLabs documents it as a stable
long-form model with Spanish support. The voice identity is centralized in settings and
versioned separately so `byte_voice_dev_v1` can later be replaced by a production identity.

The implementation uses the official `elevenlabs` SDK version resolved in `uv.lock` and the
current `text_to_speech.with_raw_response.convert` API. The raw response is used only to
capture safe response headers such as `request-id` and `character-cost`.

## Idempotency and compatibility

The existing audio fingerprint includes exact narration text, language, provider and provider
version, voice ID, voice version, model, and all exposed voice settings. Visual or caption
changes do not invalidate narration. Identical inputs reuse the stored narration artifact and
avoid another credit-consuming request. Actual duration continues to come from ffprobe, and
the existing alignment provider remains independent of ElevenLabs.

## Development and licensing boundary

Free-plan ElevenLabs outputs are development/test outputs for this phase. Commercial or public
publishing must follow the terms of the active ElevenLabs plan, and the user remains responsible
for voice and source rights. No commercial eligibility is encoded in runtime logic.

SFX and music are intentionally deferred to a separate audio identity/library slice.

## Validation and limitations

- Unit tests mock the SDK boundary and never call ElevenLabs.
- The real API smoke test is pending until an API key and voice ID are available in the local
  environment.
- The provider does not add chunking because the current short-form script fits the documented
  model limits; sentence-boundary chunking can be added if real usage demonstrates a need.
