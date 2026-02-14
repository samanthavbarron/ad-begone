<p align="center">
  <img src="logo.svg" alt="ad-begone logo" width="256" />
</p>

# ad-begone

I hate ads. I especially hate ads when I'm listening to a podcast first thing in the morning.

This Python package provides a CLI tool, `adwatch`, that watches a directory for MP3 files, detects ads in them, and removes them. It is intended for use with [Audiobookshelf](https://www.audiobookshelf.org/), which provides exactly this sort of directory.

## How it works

1. **Transcribe** -- Uses OpenAI's Whisper API to transcribe podcast audio into timestamped segments
2. **Annotate** -- Sends segments to the GPT-4o Chat Completions API with function calling to classify each segment as content or ad
3. **Trim** -- Removes ad segments from the audio and inserts a short [bell-like notification sound](https://github.com/samanthavbarron/ad-begone/blob/main/src/ad_begone/notif.mp3) where ads were removed

Files larger than 25 MB are automatically split into parts to stay within Whisper's upload limit, processed individually, then recombined.

## Cost

Most of the billing usage from OpenAI's API is due to the Whisper transcription service. Removing ads on a ~20 minute podcast costs about $0.30 (~$1/hour). Since the bottleneck is transcription and the [Whisper model is open source](https://github.com/openai/whisper), the costs could likely be improved by running Whisper locally.

## Prerequisites

- Python 3.12+
- [ffmpeg](https://ffmpeg.org/) (required by pydub for audio processing)
- An [OpenAI API key](https://platform.openai.com/api-keys) set as `OPENAI_API_KEY` in your environment

## Installation

```bash
pip install .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Usage

`adwatch` runs in a loop, scanning for new MP3 files and processing them:

```bash
# Watch a directory (checks every 10 minutes by default)
adwatch --directory /path/to/podcasts

# Custom interval (in seconds)
adwatch --directory /path/to/podcasts --sleep 300

# Watch the current directory
adwatch
```

Processed files are tracked with hidden marker files (`.hit.<filename>.txt`) so they won't be reprocessed on subsequent scans.

## Docker

A multi-stage Docker build is provided. The image uses `adwatch` as its entrypoint.

```bash
docker build -t ad-begone .
```

Or use Docker Compose (`compose.yml` included):

```bash
# Set your API key in .env or export it
export OPENAI_API_KEY=sk-...

# Place podcast files in ./podcasts/
docker compose up
```

The compose configuration mounts `./podcasts` to `/data` inside the container and runs with `restart: unless-stopped`.

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest test/ -v

# Type checking
uv run mypy src/

# Run tests with coverage
uv run pytest --cov=ad_begone test/
```

## License

[GPL-3.0](LICENSE)
