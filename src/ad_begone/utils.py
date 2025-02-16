import os
from typing import List

from openai import OpenAI
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from openai.types.chat.parsed_chat_completion import ParsedChatCompletion
from openai.types.chat.parsed_function_tool_call import ParsedFunctionToolCall

from .models import SegmentAnnotation, Window

CLIENT = None


def cached_transcription(file_name: str) -> TranscriptionVerbose:
    if ".mp3" not in file_name:
        raise ValueError("Couldn't find valid file")
    file_prefix = file_name.split(".mp3")[0]
    file_transcription = file_prefix + ".json"

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


def annotate_transcription(
    transcription: TranscriptionVerbose,
    model: str = "gpt-4o-2024-08-06",
) -> ParsedChatCompletion:
    transcription_inds = transcription_with_segment_indices(transcription)

    if os.path.isfile("test/data/test_annotation_completion.json"):
        with open("test/data/test_annotation_completion.json", "r") as f:
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
        with open("test/data/test_annotation_completion.json", "w") as f:
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