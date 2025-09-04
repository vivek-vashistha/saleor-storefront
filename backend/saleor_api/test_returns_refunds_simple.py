# test_returns_refunds_simple.py
import json
from pprint import pprint
from test_salor_graph_api import ask_graph  # reuses your /orders client

SESSION = "returns-simple"

def show(label, obj):
    pprint(f"\n== {label} ==")
    pprint(obj)

if __name__ == "__main__":
    # 1) Happy-path: “return by product name” + email in additional_details
    # r1 = ask_graph(
    #     question="I want to return 'The Dash Cushion'",
    #     additional_details="tyler.howard@example.com",  # treated as the customer's email
    #     session_id=SESSION
    # )
    # show("Return by product name (uses email)", r1)

    # # 2) Another example: natural phrasing; the tool should still do the same steps
    # r2 = ask_graph(
    #     question="I want to return 1 × 'Battle-tested at brands like Lush'",
    #     additional_details="tyler.howard@example.com",
    #     session_id=SESSION
    # )
    # show("Another phrasing", r2)

    # r1 = ask_graph(
    #     question="I want to return 1 'gret hoodie'",
    #     additional_details="steven.walsh@example.com",  # treated as the customer's email
    #     session_id=SESSION
    # )
    # show("Return by product name (uses email)", r1)


    r1 = ask_graph(
        question="I want to return 1 'apple juice'",
        additional_details="vanessa.bird@example.com",  # treated as the customer's email
        session_id=SESSION
    )
    show("Return by product name (uses email)", r1)

    