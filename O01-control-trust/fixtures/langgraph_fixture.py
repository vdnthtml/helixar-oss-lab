from __future__ import annotations
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

class State(TypedDict):
    value: int
    approved: bool
    effects: list[str]

def approval_gate(state: State):
    approved = interrupt({"proposal_id": "proposal.invalid", "value": state["value"]})
    return {"approved": bool(approved)}

def execute(state: State):
    if not state["approved"]:
        raise AssertionError("execution must stay blocked")
    return {"value": state["value"] + 1, "effects": state["effects"] + ["synthetic.invalid"]}

builder = StateGraph(State)
builder.add_node("approval_gate", approval_gate)
builder.add_node("execute", execute)
builder.add_edge(START, "approval_gate")
builder.add_edge("approval_gate", "execute")
builder.add_edge("execute", END)
graph = builder.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "o01-langgraph.invalid"}}
first = graph.invoke({"value": 1, "approved": False, "effects": []}, config)
snapshot = graph.get_state(config)
assert first["effects"] == []
assert snapshot.next == ("approval_gate",)
final = graph.invoke(Command(resume=True), config)
assert final == {"value": 2, "approved": True, "effects": ["synthetic.invalid"]}
print("PASS langgraph_interrupt_resume value=2 effects=1 pre_resume_effects=0")
