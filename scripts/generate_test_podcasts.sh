#!/usr/bin/env bash
#
# Generate fake podcast MP3s with embedded ads for use as test fixtures.
# Uses OpenAI's TTS API to synthesize speech and ffmpeg to concatenate segments.
#
# Usage:
#   ./scripts/generate_test_podcasts.sh
#
# Requires:
#   - OPENAI_API_KEY in .env (or exported)
#   - curl, ffmpeg, jq

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/test/data"
TEMP_DIR="$(mktemp -d)"

trap 'rm -rf "$TEMP_DIR"' EXIT

# Load .env if present
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "Error: OPENAI_API_KEY not set. Add it to .env or export it." >&2
    exit 1
fi

for cmd in curl ffmpeg jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is required but not installed." >&2
        exit 1
    fi
done

mkdir -p "$OUTPUT_DIR"

# ─── TTS helper ───────────────────────────────────────────────────────────────

generate_segment() {
    local text="$1"
    local output_file="$2"
    local voice="${3:-alloy}"

    echo "  Generating: $(echo "$text" | head -c 60)..."

    curl -s -o "$output_file" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg model "tts-1" \
            --arg input "$text" \
            --arg voice "$voice" \
            '{model: $model, input: $input, voice: $voice}')" \
        "https://api.openai.com/v1/audio/speech"

    # Verify we got valid audio, not an error JSON
    if file "$output_file" | grep -q "JSON\|ASCII"; then
        echo "Error generating TTS:" >&2
        cat "$output_file" >&2
        exit 1
    fi
}

# Concatenate mp3 segments using ffmpeg
concat_segments() {
    local output_file="$1"
    shift
    local segments=("$@")

    local filelist="$TEMP_DIR/filelist.txt"
    > "$filelist"
    for seg in "${segments[@]}"; do
        echo "file '$seg'" >> "$filelist"
    done

    ffmpeg -y -f concat -safe 0 -i "$filelist" -c copy "$output_file" 2>/dev/null
}

# ─── Podcast definitions ─────────────────────────────────────────────────────
#
# Each podcast is an array of (type, voice, text) triples.
# type: "content" or "ad"
# voice: OpenAI TTS voice name
# text: the spoken content

# ─── Podcast 1: "test.mp3" ── short podcast ──────────────────────────────────

podcast1_types=()
podcast1_voices=()
podcast1_texts=()

podcast1_types+=("content")
podcast1_voices+=("onyx")
podcast1_texts+=("Welcome to The Winding Path, the podcast where we explore forgotten stories from history. I'm your host, Marcus Bellweather. Today we're diving into the peculiar tale of the Cloverfield Bridge, a structure built in eighteen forty two that was somehow constructed backwards. The engineers of the time were baffled, and the townspeople were furious.")

podcast1_types+=("content")
podcast1_voices+=("onyx")
podcast1_texts+=("According to the records we found in the Dunmore County archives, the lead architect, a fellow named Reginald Pemberton, insisted the bridge was built exactly to specification. He claimed the river itself was flowing in the wrong direction. This led to a three year legal dispute that became known locally as the Pemberton Affair.")

podcast1_types+=("ad")
podcast1_voices+=("nova")
podcast1_texts+=("This episode is brought to you by Zilkora Mattresses. Are you tired of waking up feeling like you slept on a pile of rocks? Zilkora's CloudWeave technology cradles every part of your body in perfect comfort. Visit zilkora dot com slash winding and use code HISTORY for twenty percent off your first order. That's zilkora dot com slash winding. Zilkora, sleep like you mean it.")

podcast1_types+=("content")
podcast1_voices+=("onyx")
podcast1_texts+=("Now back to the Pemberton Affair. The resolution came in an unexpected way. A traveling surveyor named Abigail Marsh happened through town and demonstrated conclusively that Pemberton had simply read the blueprints upside down. The bridge was torn down and rebuilt, this time facing the correct direction. Pemberton, humiliated, relocated to another county where he became a moderately successful hat maker.")

podcast1_types+=("ad")
podcast1_voices+=("nova")
podcast1_texts+=("A quick word from our friends at Braxley's Everyday Tonic. Feeling sluggish in the afternoons? Braxley's combines twelve natural botanicals into one refreshing drink that keeps you sharp without the jitters. No artificial sweeteners, no funny business. Find Braxley's at your local grocery store or order online at braxleys dot co. Braxley's, because every day matters.")

podcast1_types+=("content")
podcast1_voices+=("onyx")
podcast1_texts+=("And that wraps up today's episode of The Winding Path. The Cloverfield Bridge still stands today, by the way, rebuilt correctly, and there's a small plaque commemorating the whole debacle. If you enjoyed this episode, please leave us a review wherever you listen to podcasts. Until next time, keep exploring the winding path.")

# ─── Podcast 2: "test_new.mp3" ── different podcast ──────────────────────────

podcast2_types=()
podcast2_voices=()
podcast2_texts=()

podcast2_types+=("content")
podcast2_voices+=("echo")
podcast2_texts+=("Hey everyone, you're listening to Tangent Mode, the show where we pick a random topic and just see where it goes. I'm Della Huang. Today's random topic, pulled straight from our fishbowl, is the invention of synthetic rubber. Now I know that doesn't sound thrilling, but trust me, this story has betrayal, explosions, and at least one very angry goat.")

podcast2_types+=("content")
podcast2_voices+=("echo")
podcast2_texts+=("So it all starts in the early nineteen hundreds. Natural rubber was an enormous industry, mostly centered around plantations in Southeast Asia. But a handful of chemists in Europe were trying to figure out how to make rubber from scratch in a laboratory. The first real breakthrough came from a researcher named Henning Voss, who accidentally polymerized isoprene while trying to make a better adhesive for wallpaper.")

podcast2_types+=("ad")
podcast2_voices+=("shimmer")
podcast2_texts+=("Before we continue, let me tell you about Fenwick Notebooks. Whether you're journaling, sketching, or planning world domination, Fenwick's premium notebooks have the smoothest paper you'll ever write on. Their signature Inkglide pages prevent bleed-through and feathering, even with fountain pens. Check them out at fenwicknotes dot com and use code TANGENT for fifteen percent off. Fenwick, put your thoughts on better paper.")

podcast2_types+=("content")
podcast2_voices+=("echo")
podcast2_texts+=("Alright, back to the rubber. So Henning Voss has this accidental polymer on his hands, literally, it was stuck to his fingers for three days. He writes up his findings but his university dismisses the work as irrelevant. Enter Klara Johanssen, a rival chemist who saw the potential immediately. She refined the process and within two years had produced the first commercially viable synthetic rubber compound.")

podcast2_types+=("content")
podcast2_voices+=("echo")
podcast2_texts+=("The angry goat I mentioned? Apparently Johanssen kept a pet goat in her laboratory, as one does, and the goat ate an entire notebook full of her formulas. She had to recreate six months of work from memory. The goat, whose name was Professor Nibbleton, was banished to a nearby farm and reportedly lived to the ripe old age of nineteen.")

podcast2_types+=("ad")
podcast2_voices+=("shimmer")
podcast2_texts+=("This episode is sponsored by Quartzy Meal Kits. Look, we all want to eat better but who has time to plan meals? Quartzy delivers pre-portioned ingredients and dead simple recipes right to your door. Each meal takes under thirty minutes and they cater to every dietary need you can think of. Head to quartzy meals dot com slash tangent to get your first box half off. Quartzy, dinner without the drama.")

podcast2_types+=("content")
podcast2_voices+=("echo")
podcast2_texts+=("And that's the story of synthetic rubber, more or less. There's a lot more to it involving wartime production and international espionage, but we'll save that for another episode. Thanks for going on this tangent with me. Hit subscribe, tell a friend, and I'll see you next week with whatever we pull out of the fishbowl. Peace.")

# ─── Podcast 3: "test_long.mp3" ── longer podcast with more segments ────────

podcast3_types=()
podcast3_voices=()
podcast3_texts=()

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("Good morning and welcome to Between the Lines, a weekly deep dive into the world of independent literature. I'm your host, Julian Ashford. On today's show, we're talking about the resurgence of serialized fiction. For decades, the publishing industry dismissed serialized stories as relics of the Victorian era, but a new generation of writers is proving that releasing novels chapter by chapter can actually build more engaged and passionate audiences.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("Our first guest today wrote an entire twelve part novella series that she released one chapter per week over the course of a year. Each installment ended on a cliffhanger, and her readership grew from about two hundred people to over forty thousand by the final chapter. She's here to tell us how she did it and what she learned along the way.")

podcast3_types+=("content")
podcast3_voices+=("nova")
podcast3_texts+=("Thanks for having me, Julian. Honestly, when I started the project, I had no idea if anyone would stick around past chapter three. The key was treating each chapter like its own self-contained episode while still advancing the larger arc. I also made a point of engaging with readers between installments, asking them questions, responding to theories, and even incorporating some of their feedback into the story.")

podcast3_types+=("ad")
podcast3_voices+=("alloy")
podcast3_texts+=("This portion of Between the Lines is brought to you by Tremelo Audio. Tremelo makes the premium earbuds designed for podcast listeners. With their StoryMode feature, voices sound natural and clear, not tinny or over-processed. Right now, listeners of this show can get twenty five percent off any Tremelo product at tremelo audio dot com slash lines. Enter code PAGES at checkout. Tremelo, hear every word.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("That's fascinating. Now you mentioned incorporating reader feedback. Can you give us an example of that? I imagine it's a delicate balance between staying true to your vision and giving the audience what they want.")

podcast3_types+=("content")
podcast3_voices+=("nova")
podcast3_texts+=("Absolutely. There was one character, a minor side character named Elden, who readers absolutely fell in love with. I had originally planned for him to appear in just two chapters, but the response was so overwhelming that I expanded his role significantly. He ended up being central to the climax of the whole series. But I was careful, I only expanded things that genuinely served the story. I never let popularity dictate a plot point that would undermine the narrative.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("That sounds like a masterclass in audience engagement. Let's talk about the business side of things. You released this for free initially. How did you eventually monetize it, and would you recommend that approach to other writers?")

podcast3_types+=("content")
podcast3_voices+=("nova")
podcast3_texts+=("So the free release was strategic. I wanted to build an audience first and worry about revenue later. Once the series was complete, I compiled it into a single volume, did a professional edit pass, and sold it as an ebook and paperback. The built-in audience meant I had thousands of people ready to buy on launch day. I also did a limited edition hardcover with bonus content that sold out in forty eight hours. So yes, giving it away first actually made me more money in the long run.")

podcast3_types+=("ad")
podcast3_voices+=("alloy")
podcast3_texts+=("A word from today's sponsor, Pinecroft Coffee Roasters. Pinecroft sources single origin beans from small farms and roasts them in micro batches for maximum flavor. Whether you like a bright citrusy light roast or a deep chocolatey dark roast, Pinecroft has something for you. Subscribe at pinecroft coffee dot com and get a free sample pack with your first order. Use code BOOKWORM for free shipping. Pinecroft, coffee worth savoring.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("Let's shift gears and talk about another trend in independent publishing. The rise of collaborative fiction, where multiple authors contribute to a shared universe. This has been happening in fan communities for years, but now we're seeing it professionalized, with structured writing teams and shared style guides.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("I recently spoke with the organizers of the Meridian Collective, a group of seven writers who co-created an expansive fantasy world. Each writer is responsible for a different region of the world, and their stories intersect and overlap in fascinating ways. The logistics alone are mind-boggling, they use shared documents, timelines, and even a custom wiki to keep everything consistent.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("What strikes me most about the Meridian Collective is how they handle creative disagreements. They told me they have a formal arbitration process. If two writers want contradictory things to happen in the shared timeline, they present their cases to the group and vote. But there's also a wildcard rule: once per series, any writer can invoke an override and push through a plot point without group approval. It keeps things unpredictable.")

podcast3_types+=("ad")
podcast3_voices+=("alloy")
podcast3_texts+=("Between the Lines is also supported by Duskwood Candles. Set the mood for your reading sessions with Duskwood's literary-inspired scent collection. Choose from fragrances like Old Library, Rainy Chapter, and Midnight Ink. Each candle burns for over sixty hours and is made from one hundred percent natural soy wax. Visit duskwood candles dot com and use code FICTION for ten dollars off orders over forty dollars. Duskwood, light up your imagination.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("Before we wrap up, I want to mention a few upcoming books from independent authors that I'm particularly excited about. First, there's The Cartographer's Dilemma by Soren Blackwell, a mystery set in a fictional mapping agency where the maps keep changing overnight. Then we have Rust and Reverie by Amara Osei, a post-industrial fantasy about a blacksmith who discovers her metalwork is coming to life.")

podcast3_types+=("content")
podcast3_voices+=("fable")
podcast3_texts+=("And that's our show for today. Thanks so much to our guest for joining us and sharing her insights on serialized fiction. If you want to support Between the Lines, the best thing you can do is share this episode with a fellow book lover. You can also find us on all the usual social platforms. I'm Julian Ashford, and until next time, keep reading between the lines.")

# ─── Generation loop ──────────────────────────────────────────────────────────

generate_podcast() {
    local name="$1"
    local output_mp3="$OUTPUT_DIR/$name.mp3"
    local output_transcript="$OUTPUT_DIR/$name.transcript.txt"
    shift

    local -n types_ref="$1"
    local -n voices_ref="$2"
    local -n texts_ref="$3"

    local count=${#types_ref[@]}
    local segment_files=()

    echo ""
    echo "=== Generating $name.mp3 ($count segments) ==="

    # Write transcript header
    echo "# Transcript: $name" > "$output_transcript"
    echo "" >> "$output_transcript"

    for (( i=0; i<count; i++ )); do
        local seg_type="${types_ref[$i]}"
        local voice="${voices_ref[$i]}"
        local text="${texts_ref[$i]}"

        local seg_file="$TEMP_DIR/${name}_seg_${i}.mp3"

        echo "[$seg_type] (voice: $voice)" >> "$output_transcript"
        echo "$text" >> "$output_transcript"
        echo "" >> "$output_transcript"

        generate_segment "$text" "$seg_file" "$voice"
        segment_files+=("$seg_file")
    done

    echo "  Concatenating ${#segment_files[@]} segments..."
    concat_segments "$output_mp3" "${segment_files[@]}"

    local size
    size=$(du -h "$output_mp3" | cut -f1)
    echo "  Done: $output_mp3 ($size)"
    echo "  Transcript: $output_transcript"
}

echo "Generating test podcast fixtures..."
echo "Output directory: $OUTPUT_DIR"

generate_podcast "test" podcast1_types podcast1_voices podcast1_texts
generate_podcast "test_new" podcast2_types podcast2_voices podcast2_texts
generate_podcast "test_long" podcast3_types podcast3_voices podcast3_texts

echo ""
echo "All podcasts generated successfully."
echo ""
echo "Files:"
ls -lh "$OUTPUT_DIR"/*.mp3 "$OUTPUT_DIR"/*.txt 2>/dev/null
