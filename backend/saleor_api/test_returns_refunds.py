# test_returns_refunds.py
import json
from pprint import pprint
from test_salor_graph_api import ask_graph  # uses /orders under the hood  :contentReference[oaicite:1]{index=1}
from pprint import pprint

SESSION = "returns-demo"

def pretty(label, obj):
    pprint(f"\n== {label} ==")
    pprint(json.dumps(obj, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # A) Get newest order + fulfillment context for a customer
    r1 = ask_graph(
        question=(
            "For customer tyler.howard@example.com: "
            "Fetch newest order (first:1, sort DESC) with id,status,statusDisplay, "
            "fulfillments{id status lines{id orderLine{id} quantity}}, "
            "and lines{id productName quantity quantityFulfilled unitPrice{gross{amount currency}}}."
        ),
        session_id=SESSION
        # backend_url="http://localhost:8002/orders",  # optional override
    )
    pretty("Step 1 — Fulfillment status", r1)

    # B) Return + refund by product name (tool should resolve fulfillmentLineId and amountToRefund)
    r2 = ask_graph(
        question=(
            "Create a return with refund for 1 unit of 'The Dash Cushion' from that newest fulfilled order. "
            "If the order is not fulfilled, respond that it must be fulfilled first and stop. "
            "Otherwise compute amountToRefund = unitPrice.gross.amount * quantity (2 decimals) and call "
            "orderFulfillmentReturnProducts(order, input:{fulfillmentLines, amountToRefund, refund:true}). "
            "Return returnFulfillment{id status}, order{status}, errors{field message}."
        ),
        session_id=SESSION
    )
    pretty("Step 2 — Return+Refund by product name", r2)

    # C) Return + refund by known fulfillmentLineId (supply orderId + FL id)
    r3 = ask_graph(
        question=(
            "Return and refund quantity:1 using fulfillmentLineId=<PUT_FULFILLMENT_LINE_ID_HERE> "
            "for order id <PUT_ORDER_ID_HERE>; refund:true. "
            "Compute amountToRefund from that line's unitPrice * qty. "
            "Call orderFulfillmentReturnProducts and return returnFulfillment{id status}, "
            "order{status}, errors{field message}."
        ),
        session_id=SESSION
    )
    pretty("Step 3 — Return+Refund by fulfillmentLineId", r3)

    # Optional: extract the 'Final response' block your app returns
    if isinstance(r1, dict):
        data = r1.get("data", {})
        answer_block = data.get("answer", "")
        final_answer = answer_block.split("### Final response", 1)[1].strip() if "### Final response" in answer_block else None
        print("\n== Final response ==\n", final_answer or answer_block)
