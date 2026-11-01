# TaigerDesignClaude — working notes for Claude

## Video sound design (apply to every video/animation task)

Claude can't hear audio, so sound effects it picks or synthesizes by guesswork tend to be bad. For any video, animation or motion-graphics deliverable, use this order:

1. **Sound plan first.** Before rendering, list every moment that needs sound (cuts, impacts, UI pops, whooshes, text reveals, transitions) with its timestamp. Keep it in `sound_plan.json`: `[{ "t": 1.20, "cue": "whoosh", "desc": "card slides in from left", "dur": 0.4 }]`.
2. **Real recordings: Openverse API.** Search `https://api.openverse.org/v1/audio/?q=<term>&license_type=commercial`. Only use CC0, CC BY or CC BY-SA files. Write each file's title, creator, license and URL to `CREDITS.md` (CC BY requires attribution).
3. **Code-made sounds: earshot** (MIT, https://github.com/Leonxlnx/earshot). Use it when nothing on Openverse fits. It has a bank of about 250 code-rendered SFX, a `forge` command that synthesizes a sound and runs a critic loop, and a `timeline` command that "listens" to a finished render and reports sound events and sync against picture cuts.
4. **Mix with ffmpeg.** Place each cue at its timestamp (`adelay`), duck it under any music or voiceover, then normalize loudness to -14 LUFS for social (`loudnorm=I=-14:TP=-1.5`).
5. **Verify.** Run earshot `timeline` (or ffmpeg `silencedetect`/`ebur128`) on the final export and check every cue lands within ~1 frame of its visual.

Don't use "Opus Sound Layer". It isn't a Claude or Anthropic feature. The closest real thing is OpusClip's auto-SFX, a separate paid product.

### Environment prerequisites (cloud sessions)
- The network allowlist needs `api.openverse.org`, plus `pypi.org`/`github.com` to install earshot.
- Installing earshot is third-party code, so it needs the user's approval in the session.
- ffmpeg is already available.
