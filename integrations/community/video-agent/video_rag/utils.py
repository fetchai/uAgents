from typing import List
import math
import tiktoken
import spacy
import structlog
from urllib.parse import parse_qs, urlparse
from youtube_transcript_api import YouTubeTranscriptApi


logger = structlog.get_logger("utils")

nlp = spacy.load("en_core_web_lg", disable=["parser", "ner"])
spacy_words = set(nlp.vocab.strings)


def cleaning_fix_unwanted_space_v2(_inp_str: str) -> str:
    _vacob = spacy_words

    _inp_str_splitted = _inp_str.split()
    out_words = []

    i = 0
    while i < len(_inp_str_splitted):
        word = _inp_str_splitted[i]

        if word not in _vacob and i + 1 < len(_inp_str_splitted):
            next_word = _inp_str_splitted[i + 1]
            joined = word + next_word

            if joined.strip() in _vacob:
                word = joined
                i += 1
            else:
                if (i - 1) > 0:
                    prev_word = _inp_str_splitted[i - 1]
                    joined = prev_word + word

                    if joined.strip() in _vacob:
                        word = joined
                        del out_words[-1]

        out_words.append(word)
        i += 1

    return " ".join(out_words)


def split_string_into_chunks(input_string, max_tokens=4096):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(input_string)

    chunks = []
    current_chunk = []

    for token in tokens:
        if len(chunks) == 0:
            if len(current_chunk) <= max_tokens - 1000:
                current_chunk.append(token)
            else:
                print(len(current_chunk))
                chunks.append(encoding.decode(current_chunk))
                current_chunk = []
                current_chunk.append(token)
        else:
            if len(current_chunk) <= max_tokens:
                current_chunk.append(token)
            else:
                print(len(current_chunk))
                chunks.append(encoding.decode(current_chunk))
                current_chunk = []
                current_chunk.append(token)

    return chunks


def get_batches(transcript: List[str], token_limit):
    transcript_str = "".join(transcript)

    # estimate size of the transcript
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(transcript_str)
    num_tokens = len(tokens)

    # output should be shorter then the input, so we can split 60% input, 40% output
    max_input_tokens = int(token_limit * 0.6)

    # how many chunks we will need
    num_chunks = math.ceil(num_tokens / max_input_tokens)

    if num_chunks <= 1:
        logger.info(
            f"Transcript is small enough to fit in one batch: tokens={num_tokens}"
        )
        return num_tokens, [cleaning_fix_unwanted_space_v2(transcript_str)]

    # the limit of characters in one batch
    token_limit_per_batch = int(len(tokens) / num_chunks)

    logger.info(
        f"Transcript is too big, splitting into {num_chunks} chunks, {token_limit_per_batch} tokens per batch!"
    )

    # lets create batches
    batches = []

    current_batch = []
    current_batch_size = 0
    for line in transcript:
        len_line = len(encoding.encode(line))
        if (current_batch_size + len_line) < token_limit_per_batch:
            current_batch.append(line)
            current_batch_size += len_line
        else:
            batches.append(cleaning_fix_unwanted_space_v2("".join(current_batch)))
            current_batch = [line]
            current_batch_size = len_line
    if len(current_batch) > 0:
        batches.append(cleaning_fix_unwanted_space_v2("\n".join(current_batch)))

    return num_tokens, batches


def get_video_script(url):
    if not url:
        raise ValueError("YouTube video url is required")

    parsed_url = urlparse(url)

    query_params = parse_qs(parsed_url.query)

    video_id = None

    if "v" in query_params:
        video_id = query_params["v"][0]
    else:
        raise ValueError("YouTube video ID not found in the URL")

    if not video_id:
        raise ValueError("YouTube video ID not found in the URL")

    scripts = YouTubeTranscriptApi.get_transcript(
        video_id, languages=("en", "en-US", "en-GB")
    )

    return [item["text"] for item in scripts]
