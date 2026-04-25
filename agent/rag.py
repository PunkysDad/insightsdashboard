import os
import pathlib

import anthropic
from dotenv import load_dotenv
from pinecone import Pinecone

from insight_engine.engine import MODELS

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
EMBEDDING_MODEL = "llama-text-embed-v2"

SYSTEM_PROMPT = """You are a knowledgeable and friendly destination concierge assistant. Your job is to help visitors plan their trip, discover things to do, find places to eat, locate hotels, and explore local events. Answer based on the provided destination context. If you don't have specific information, say so honestly and suggest the visitor check the destination's official website. Keep responses conversational, helpful, and concise."""

USER_TEMPLATE = """Context from destination knowledge base:
{context}

Visitor question: {user_message}"""

NO_CONTEXT_FALLBACK = "No relevant context found."


def retrieve_context(query: str, client_id: str, top_k: int = 5) -> str:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    embeddings = pc.inference.embed(
        model=EMBEDDING_MODEL,
        inputs=[query],
        parameters={"input_type": "query"},
    )
    vector = embeddings[0].values

    results = index.query(
        vector=vector,
        top_k=top_k,
        filter={"client_id": client_id},
        include_metadata=True,
    )

    chunks = []
    for match in results.matches:
        metadata = match.metadata or {}
        text = metadata.get("text")
        if text:
            chunks.append(text)

    if not chunks:
        return NO_CONTEXT_FALLBACK

    return "\n\n---\n\n".join(chunks)


def build_messages(conversation_history: list[dict], user_message: str, context: str) -> list[dict]:
    messages = list(conversation_history)
    messages.append(
        {
            "role": "user",
            "content": USER_TEMPLATE.format(context=context, user_message=user_message),
        }
    )
    return messages


async def stream_response(
    session_id: str,
    conversation_history: list[dict],
    user_message: str,
    client_id: str,
):
    context = retrieve_context(user_message, client_id)
    messages = build_messages(conversation_history, user_message, context)

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODELS["agent"],
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for chunk in stream.text_stream:
            yield f"data: {chunk}\n\n"

    yield "data: [DONE]\n\n"
