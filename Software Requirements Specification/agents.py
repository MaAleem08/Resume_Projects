import os
from typing import TypedDict, List
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END
from vector_store import vector_store

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"


class PipelineState(TypedDict):
    raw_text: str
    requirements: List[str]
    classified: List[dict]
    document: str


def call_llm(prompt):
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL_NAME,
    )
    return response.choices[0].message.content


# Agent 1: pulls out individual requirement statements from raw notes
def extractor_node(state: PipelineState):
    prompt = f"""Extract individual software requirements from the notes below.
Return each requirement on its own line. No numbering, no headings, no extra text.

Notes:
{state['raw_text']}
"""
    result = call_llm(prompt)
    lines = [line.strip("-• ").strip() for line in result.split("\n") if line.strip()]
    state["requirements"] = lines
    return state


# Agent 2: labels each requirement and checks it against past requirements in FAISS
def classifier_node(state: PipelineState):
    classified = []

    for req in state["requirements"]:
        prompt = f"""Classify the requirement below as exactly one word: "Functional" or "Non-Functional".

Requirement: {req}
"""
        req_type = call_llm(prompt).strip()

        similar = vector_store.find_similar(req)
        issues = f"Possible duplicate of: '{similar}'" if similar else ""

        classified.append({"text": req, "req_type": req_type, "issues": issues})
        vector_store.add(req)

    state["classified"] = classified
    return state


# Agent 3: flags vague/ambiguous requirements
def reviewer_node(state: PipelineState):
    for item in state["classified"]:
        prompt = f"""Is the requirement below ambiguous or unclear?
If yes, explain why in one short line. If it is clear, reply with only: OK

Requirement: {item['text']}
"""
        review = call_llm(prompt).strip()
        if review.upper() != "OK":
            item["issues"] = f"{item['issues']} | {review}".strip(" |") if item["issues"] else review

    return state


# Agent 4: turns the reviewed requirement list into an SRS-style markdown document
def doc_generator_node(state: PipelineState):
    req_lines = "\n".join(
        f"- [{item['req_type']}] {item['text']}" for item in state["classified"]
    )

    prompt = f"""Write a short Software Requirements Specification in markdown using the
requirements below. Include these sections: Introduction, Functional Requirements,
Non-Functional Requirements, Known Issues.

Requirements:
{req_lines}
"""
    state["document"] = call_llm(prompt)
    return state


def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("extractor", extractor_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("doc_generator", doc_generator_node)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "classifier")
    graph.add_edge("classifier", "reviewer")
    graph.add_edge("reviewer", "doc_generator")
    graph.add_edge("doc_generator", END)

    return graph.compile()


pipeline = build_pipeline()
