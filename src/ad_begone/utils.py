import os
from typing import List

from openai import OpenAI
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from openai.types.chat.parsed_chat_completion import ParsedChatCompletion
from openai.types.chat.parsed_function_tool_call import ParsedFunctionToolCall
from pydub import AudioSegment

from .models import SegmentAnnotation, Window

CLIENT = None


def cached_transcription(
    file_name: str,
    file_transcription: str | None = None,
) -> TranscriptionVerbose:
    if ".mp3" not in file_name:
        raise ValueError("Couldn't find valid file")

    if file_transcription is None:
        file_transcription = file_name.split(".mp3")[0] + ".json"

    if os.path.isfile(file_transcription):
        with open(file_transcription, "r") as f:
            return TranscriptionVerbose.parse_raw(f.read())

    audio_file = open(file_name, "rb")

    transcription: TranscriptionVerbose = CLIENT.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["segment"]
    )

    with open(file_transcription, "w") as f:
        f.write(transcription.model_dump_json())

    return transcription


def transcription_with_segment_indices(transcription: TranscriptionVerbose) -> str:
    res = ""
    for idx, segment in enumerate(transcription.segments):
        _segment = segment.text.rstrip(" ")
        _segment = segment.text.lstrip(" ")
        res += f"Segment {idx}: {_segment}\n"
    return res


def cached_annotate_transcription(
    transcription: TranscriptionVerbose,
    file_name: str,
    model: str = "gpt-4o-2024-08-06",
) -> ParsedChatCompletion:
    transcription_inds = transcription_with_segment_indices(transcription)

    if os.path.isfile(file_name):
        with open(file_name, "r") as f:
            _text = f.read()
        completion = ParsedChatCompletion.parse_raw(_text)
    else:
        system_prompt = """You are a helpful assistant.
        You help users identify segments in a transcription that are ads or content.
        You will be given a transcription and asked to annotate the segments as either ads or content.
        You ONLY need to provide annotations for the segments at the beginning of each ad or content block.
        """
        user_prompt = f"Please annotate following transcription with the segments that are ads or content:\n{transcription_inds}"

        completion: ParsedChatCompletion = CLIENT.beta.chat.completions.parse(
            model=model,
            messages=[
                { "role": "system", "content": system_prompt, },
                { "role": "user", "content": user_prompt, },
            ],
            tools=[ CLIENT.pydantic_function_tool(SegmentAnnotation), ],
        )
        with open(file_name, "w") as f:
            f.write(completion.model_dump_json())

    return completion


def get_ordered_annotations(completion: ParsedChatCompletion) -> list[SegmentAnnotation]:
    tool_calls: List[ParsedFunctionToolCall] = completion.choices[0].message.tool_calls

    annotations: list[SegmentAnnotation] = []

    for tool_call in tool_calls:
        fn = tool_call.function
        if fn.name == "SegmentAnnotation":
            annotations.append(SegmentAnnotation.model_validate(fn.parsed_arguments))

    return list(sorted(annotations, key=lambda ann: ann.segment_index))


def find_ad_time_windows(
    transcription: TranscriptionVerbose,
    annotations: list[SegmentAnnotation],
) -> list[Window]:
    windows = []

    current_time = 0.0
    current_segment_type = None
    for ann in annotations:
        seg = transcription.segments[ann.segment_index]
        if current_segment_type is None:
            current_segment_type = ann.segment_type

        if current_segment_type != ann.segment_type:
            windows.append(Window(start=current_time, end=seg.start, segment_type=current_segment_type))
            current_segment_type = ann.segment_type
        current_time = seg.end

    windows.append(Window(start=current_time, end=transcription.segments[-1].end, segment_type=current_segment_type))

    return windows


def split_mp3(
    file_name: str,
    file_name_transcription_cache: str,
    out_name: str | None = None,
    notif_name: str = "test/data/notif.mp3",
):
    transcription = cached_transcription(file_name)
    completion = cached_annotate_transcription(transcription, file_name=file_name_transcription_cache)
    annotations = get_ordered_annotations(completion)
    windows = find_ad_time_windows(transcription, annotations)

    audio = AudioSegment.from_mp3(file_name)
    notif = AudioSegment.from_mp3(notif_name)
    kept_windows = []
    for window in windows:
        if window.segment_type == "content":
            kept_windows.append(audio[window.start * 1000: window.end * 1000])
        if window.segment_type == "ad":
            kept_windows.append(notif)

    audio_no_ads = AudioSegment.silent(duration=0)
    for kept_window in kept_windows:
        audio_no_ads += kept_window

    if out_name is None:
        out_name = file_name.split(".")[0] + "_no_ads.mp3"

    audio_no_ads.export(out_name, format="mp3")