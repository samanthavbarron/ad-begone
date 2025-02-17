import os
from pathlib import Path
from typing import List

import numpy as np
from openai import OpenAI, pydantic_function_tool
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from openai.types.chat.parsed_chat_completion import ParsedChatCompletion
from openai.types.chat.parsed_function_tool_call import ParsedFunctionToolCall
from pydub import AudioSegment

from .models import SegmentAnnotation, Window
from .notif_path import NOTIF_PATH

CLIENT = OpenAI()


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

    print("Transcribing audio...")
    transcription: TranscriptionVerbose = CLIENT.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["segment"]
    )

    with open(file_transcription, "w") as f:
        f.write(transcription.model_dump_json())

    print("Got transcription")
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

        print("Annotating transcription...")
        completion: ParsedChatCompletion = CLIENT.beta.chat.completions.parse(
            model=model,
            messages=[
                { "role": "system", "content": system_prompt, },
                { "role": "user", "content": user_prompt, },
            ],
            tools=[ pydantic_function_tool(SegmentAnnotation), ],
        )
        with open(file_name, "w") as f:
            f.write(completion.model_dump_json())
        print("Got annotations")

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


def _remove_ads(
    file_name: str,
    file_name_transcription_cache: str,
    out_name: str | None = None,
    notif_name: str = NOTIF_PATH,
) -> str:
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
        if "part_" not in file_name:
            raise ValueError("Destructive")
        out_name = file_name

    audio_no_ads.export(out_name, format="mp3")
    return out_name


def split_file(
    file_name: str,
    max_file_size_mb: float = 25.0,
) -> list[str]:
    max_file_size_mb = 25.0
    file_path = Path(file_name)
    audio = AudioSegment.from_mp3(file_name)
    file_size = os.path.getsize(file_name) / 1024 / 1024
    total_splits = int(np.ceil(file_size / max_file_size_mb))
    def _split_i(i):
        start = int(i * len(audio) / total_splits)
        end = int((i + 1) * len(audio) / total_splits)
        return audio[start:end]

    split_file_names = []
    for i in range(total_splits):
        _fn = file_path.parent / f"part_{i}_{file_path.name}"
        split_file_names.append(str(_fn))
        _split_i(i).export(_fn, format="mp3")
    return split_file_names


def join_files(
    file_name: str,
    overwrite: bool = True,
) -> str:
    path = Path(file_name)
    file_parts = []
    for fn in path.parent.glob("part_*_" + path.name):
        file_parts.append(str(fn))
    audio = AudioSegment.silent(duration=0)
    for file_part in file_parts:
        audio += AudioSegment.from_mp3(file_part)
    if overwrite:
        joined_out = path
    else:
        joined_out = path.parent / ("joined_" + path.name)
    joined_out_name = str(joined_out)
    audio.export(joined_out_name, format="mp3")
    for file_part in file_parts:
        os.remove(file_part)
    return joined_out_name