import os
import json
from typing import Any, List, Optional, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode

# Use GraphQL wrapper + tool from langchain_community
from langchain_community.utilities.graphql import GraphQLAPIWrapper
from langchain_community.tools.graphql.tool import BaseGraphQLTool

import logging
import requests

class LengthFilter(logging.Filter):
    def __init__(self, max_length):
        super().__init__()
        self.max_length = max_length

    def filter(self, record):
        # Only allow log messages up to max_length characters
        return len(record.getMessage()) <= self.max_length

# Get the gql transport logger
logger = logging.getLogger("gql.transport.requests")

# Set level to INFO so short messages still show
logger.setLevel(logging.INFO)

# Add our length filter
# logger.addFilter(LengthFilter(max_length=2500))
logger.addFilter(LengthFilter(max_length=250))

# ---------------------------------
# Config
# ---------------------------------
SALEOR_ENDPOINT = os.getenv("SALEOR_ENDPOINT", "https://store-gqt4azfa.saleor.cloud/graphql/")
SALEOR_TOKEN    = os.getenv("SALEOR_TOKEN", "REPLACE_WITH_YOUR_API_TOKEN")
CHANNEL_SLUG    = os.getenv("CHANNEL_SLUG", "default-channel")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


EXTERNAL_KG_CONTEXT: Any = None
EXTERNAL_KG_MESSAGE: Optional[str] = None

def set_external_kg_context(ctx: Any) -> None:
    """
    Receives the KG context. Normalizes and stores the human-readable 'message'
    so the LLM can use it as background context.
    """
    global EXTERNAL_KG_CONTEXT, EXTERNAL_KG_MESSAGE
    EXTERNAL_KG_CONTEXT = ctx
    EXTERNAL_KG_MESSAGE = None

    # Extract the most useful human text
    try:
        msg = None
        if isinstance(ctx, dict):
            # Prefer data.message, then fall back to top-level message
            data = ctx.get("data") or {}
            msg = data.get("message") or ctx.get("message")
        elif isinstance(ctx, str):
            msg = ctx
        if msg is not None:
            EXTERNAL_KG_MESSAGE = str(msg).strip()
    except Exception:
        pass

    # Log a compact receipt
    try:
        preview = None
        if isinstance(ctx, dict):
            preview = {
                "status": ctx.get("status"),
                "has_message": bool(EXTERNAL_KG_MESSAGE),
                "message_preview": (EXTERNAL_KG_MESSAGE[:240] + "…") if EXTERNAL_KG_MESSAGE and len(EXTERNAL_KG_MESSAGE) > 240 else EXTERNAL_KG_MESSAGE,
            }
        else:
            preview = str(ctx)[:240]
        logger.info(f"SALEOR_TOOL | kg_context_received | {json.dumps(preview)}")
    except Exception:
        logger.info("SALEOR_TOOL | kg_context_received | <unserializable>")

def get_external_kg_message() -> Optional[str]:
    """Returns the normalized KG message (if any)."""
    return EXTERNAL_KG_MESSAGE

# ---------------------------------
# GraphQL tool (UNCHANGED DESCRIPTION)
# ---------------------------------
headers = {"Authorization": f"Bearer {SALEOR_TOKEN}"} if SALEOR_TOKEN and SALEOR_TOKEN != "REPLACE_WITH_YOUR_API_TOKEN" else None
graphql_wrapper = GraphQLAPIWrapper(
    graphql_endpoint=SALEOR_ENDPOINT,
    custom_headers=headers,
    fetch_schema_from_transport=True,
)

graphql_tool = BaseGraphQLTool(
    graphql_wrapper=graphql_wrapper,
    description=(
        "If a list of product IDs (kg_products) is provided, you MUST generate exactly ONE bulk query. "
        "Use the following structure, ensuring $ids contains the COMPLETE list of provided product IDs:\n\n"
        "query ProductDetails($ids: [ID!]) {\n"
        "  products(first: 10, filter: { ids: $ids }) {\n"
        "    edges {\n"
        "      node {\n"
        "        id\n"
        "        name\n"
        "        slug\n"
        "        description\n"
        "        channelListings {\n"
        "          channel {\n"
        "            slug\n"
        "            name\n"
        "          }\n"
        "          pricing {\n"
        "            priceRange {\n"
        "              start { gross { amount currency } }\n"
        "              stop  { gross { amount currency } }\n"
        "            }\n"
        "          }\n"
        "          isAvailableForPurchase\n"
        "          isPublished\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        "Never generate individual queries for each product when kg_products is provided. "
        "Never omit any IDs from the list.\n\n"

        "Input is a valid Saleor GraphQL query/mutation string. "
        "For ANY availability/publication/pricing, ALWAYS pass the channel argument "
        f'and call product(..., channel: \"{CHANNEL_SLUG}\"). '
        "Never use isAvailable without a channel. Prefer Product.channelListings "
        "for the target channel (isPublished, availableForPurchaseAt, visibleInListings)."

        # new_salor_graph.py  (extend the existing description string passed to BaseGraphQLTool)

        """
        — ORDERS / RETURNS / REFUNDS (STRICT RULES) —

        When the user asks to check fulfillment, return products, or refund:
        1) For lookups by email:
        - Use: orders(first: N, filter: { search: "<email>" })
        - Relay connections REQUIRE pagination (first / last). Include first: 1…50.
        - For a single, newest order, add: sortBy: { field: CREATED_AT, direction: DESC }, first: 1.

        2) Always fetch fulfillment context before attempting a return:
        query OrderWithFulfillments($id: ID!) {
            order(id: $id) {
            id
            status
            fulfillments { id status lines { id orderLine { id } quantity } }
            lines {
                id productName quantity
                quantityFulfilled
                unitPrice { gross { amount currency } }
                totalPrice { gross { amount currency } }
            }
            }
        }

        3) For RETURNS with REFUND (fulfilled items only), use:
        mutation ReturnProducts($order: ID!, $input: OrderReturnProductsInput!) {
            orderFulfillmentReturnProducts(order: $order, input: $input) {
            returnFulfillment { id status }
            order { id status }
            errors { field message }
            }
        }
        input must include:
        - fulfillmentLines: [{ fulfillmentLineId: ID!, quantity: Int! }, ...]
        - amountToRefund: PositiveDecimal!
        - refund: true

        4) For REFUNDS only (fulfilled items), use:
        mutation RefundProducts($order: ID!, $input: OrderRefundProductsInput!) {
            orderFulfillmentRefundProducts(order: $order, input: $input) {
            fulfillment { id status }
            order { id status }
            errors { field message }
            }
        }
        input must include:
        - lines: [{ orderLineId: ID!, quantity: Int! }, ...] OR fulfillmentLines variant (depending on schema)
        - amountToRefund: PositiveDecimal!

        5) For whole-order refund (no line targeting), use:
        mutation OrderRefund($id: ID!, $amount: PositiveDecimal!) {
            orderRefund(id: $id, amount: $amount) {
            order { id status }
            errors { field message }
            }
        }

        6) IMPORTANT SCHEMA NOTES:
        - DO NOT use orderLineId inside "fulfillmentLines". Use fulfillmentLineId for returns based on fulfilled items.
        - If order is UNCONFIRMED/UNFULFILLED and no fulfillments exist, DO NOT call return/refund mutations. Reply with guidance to fulfill first.
        - Always include pagination args on connections (e.g., orders(first: 10)).
        - When computing refund amounts, fetch unitPrice.gross.amount and multiply by quantity; round to 2 decimals.

        7) Output JSON from the tool calls must include the errors field when present so the app can show the message.
        """


        """
        — PAYMENTS / TRANSACTIONS (CHECK BEFORE REFUND) —

        Before calling a refund or return+refund mutation:
        - Fetch order transactions to ensure there is a refundable, captured amount.
        Example fields to fetch (schema evolves; use what exists on your instance):
        order(id: $id) {
            id
            transactions {
            id
            chargedAmount { amount currency }   # or totalCharged if present
            authorizedAmount { amount currency }# optional
            status                               # optional
            }
        }

        If refund via `orderFulfillmentReturnProducts(..., refund:true)` fails with errors like
        "Order cannot be refunded", switch to the Granted Refund flow:

        1) GRANT the refund:
        mutation orderGrantRefundCreate(id: $orderId, input: {
            # include either fulfillment lines (for fulfilled items) or order lines (if supported)
            # and the amount you want to refund
            amount: $amountToRefund
            # starting from Saleor 3.20–3.21 transactionId may be required
            transactionId: $transactionId
            # includeShippingCosts: false (optional)
        }) { errors { field message } grantedRefund { id } }

        2) REQUEST the refund from the payment app:
        mutation transactionRequestRefundForGrantedRefund(
            id: $transactionId,  # or token: $transactionToken
            grantedRefundId: $grantedRefundId
        ) { errors { field message } transaction { id } }

        Notes:
        - Use `fulfillmentLines[{ fulfillmentLineId, quantity }]` for returns from fulfilled items.
        - Always provide `amountToRefund` (2 decimals).
        - If no fulfillments exist (UNCONFIRMED/UNFULFILLED), DO NOT attempt refund/return; explain that fulfillment is required first.
        """


    )
)


TOOLS = [graphql_tool]

# ---------------------------------
# Structured input helper
# ---------------------------------
@dataclass
class StructuredInput:
    users_query: str
    additional_details: Optional[str] = None
    kg_products: Optional[Any] = None
    kg_response: Optional[Any] = None


def _render_structured_input(si: StructuredInput) -> str:
    def _fmt(obj: Any) -> str:
        if obj is None:
            return "N/A"
        try:
            if isinstance(obj, str):
                return obj
            return json.dumps(obj, ensure_ascii=False)[:4000]
        except Exception:
            return str(obj)[:4000]

    return (
        "# INPUTS\n"
        f"Users query: {si.users_query}\n"
        f"Additional details: {_fmt(si.additional_details)}\n"
        f"KG products: {_fmt(si.kg_products)}\n"
        f"KG response: {_fmt(si.kg_response)}\n"
    )

def build_bulk_product_query(ids: List[str]) -> str:
    return f"""
    query ProductDetails($ids: [ID!]) {{
      products(first: {len(ids)}, filter: {{ ids: $ids }}) {{
        edges {{
          node {{
            id
            name
            slug
            description
            channelListings {{
              channel {{
                slug
                name
              }}
              pricing {{
                priceRange {{
                  start {{ gross {{ amount currency }} }}
                  stop {{ gross {{ amount currency }} }}
                }}
              }}
              isAvailableForPurchase
              isPublished
            }}
          }}
        }}
      }}
    }}
    """


# ---------------------------------
# System prompt: simplified flow + strict output
# ---------------------------------

SYSTEM_PROMPT = f"""
You are a Saleor shopping copilot for online retailers. You have exactly ONE tool: query_graphql. You may call it multiple times per turn.

HOW TO USE THE INPUT
- Each user turn is provided in this structure: "Users query", "Additional details", "KG products" (optional), and "KG response" (optional).
- Treat the two KG sections as helpful background only; ALWAYS verify details (esp. price/currency and channel data) via Saleor GraphQL.
- If query is related to the customer orders you can just used the email id to fetch the orders details.

WHAT TO DO (simplified flow)
1) Read the Inputs. Combine "Users query" + "Additional details" (+KG if present).
2) If `KG products` (list of product IDs) is provided:
- You MUST generate exactly ONE bulk GraphQL query.
- The query must use `products(filter: {{ ids: $ids }})`.
- `$ids` MUST include the COMPLETE list of product IDs from `kg_products` exactly as provided.
- Do NOT split them into multiple queries.
- Do NOT omit or reformat any IDs.
- Do NOT generate additional tool calls for these products.

3) Otherwise, proceed with the normal flow:
   - Decide what is missing to fully answer.
   - Generate one or more sub-queries (GraphQL) to fetch anything missing and/or final data.
4) Call the GraphQL tool for each sub-query. You MAY call it multiple times.
5) Summarize tool outputs and return the final answer.

OUTPUT FORMAT (must match EXACTLY; no extra sections)
### Inputs
- users_query: <verbatim from input>
- additional_details: <short>
- kg_products: <short or N/A>
- kg_response: <short or N/A>

### Generated queries
<One bullet per sub-query. Always include the full KG product list (if provided) exactly as it was given. 
For example: "Fetch product details for these products [<full list from kg_products>]" 
instead of using a placeholder like `$ids`. Do NOT shorten, omit, or reformat the IDs.>


### Tool call responses
<One short bullet block per sub-query: 1–3 bullets summarizing the key data returned (product names/IDs, availability, currency and price ranges, etc.).>

### Final response
<Concise, user-facing answer that directly addresses the original request. Include currency/channel where relevant.>


— RETURN / REFUND PLAYBOOK —
If the user asks to create a return/refund (by email, order number, or IDs):

**USE `additional_details` as the customer email if it matches an email pattern.**
- First query: orders(first: 1, filter: {{ search: "<email>" }}, sortBy: {{ field: CREATED_AT, direction: DESC }})
- Then fetch the chosen order by id with: status, fulfillments {{ id status lines {{ id orderLine {{ id }} quantity }} }}, 
  lines {{ id productName quantity quantityFulfilled unitPrice {{ gross {{ amount currency }} }} }},
  **and transactions {{ id chargedAmount {{ amount currency }} }}** if available.

C) If there are NO fulfillments or status is UNCONFIRMED/UNFULFILLED:
   - Do NOT call any refund/return mutations.
   - Reply that the order must be fulfilled first.

D) Map items:
   - For RETURNS (fulfilled items): use fulfillment.lines.id as fulfillmentLineId.

E) Compute amountToRefund:
   - If user provides an explicit amount, use it.
   - Else compute sum(unitPrice.gross.amount * quantity) for the selected lines; round(…, 2).

F) Try single-step return+refund first:
   - orderFulfillmentReturnProducts(order, input: {{ fulfillmentLines, amountToRefund, refund: true }})
   - Always include errors {{ field, message }}.

**G) If errors indicate refund isn’t possible (e.g., "Order cannot be refunded") or there is no refundable charged amount:**
   1) Create a granted refund with orderGrantRefundCreate(id: $orderId, input: {{
        amount: $amountToRefund,
        transactionId: $transactionId  # if required by your Saleor version
      }})
   2) Request the refund against that grant with transactionRequestRefundForGrantedRefund(
        id: $transactionId,
        grantedRefundId: $grantedRefundId
      )
   - Include errors {{ field, message }} in both steps.

Relay rule: EVERY connection MUST include first/last to paginate.
Never invent field names. Prefer fields shown in the tool description.
"""

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0).bind_tools(TOOLS)

# ---------------------------------
# Minimal graph
# ---------------------------------

def _sanitize_for_llm(messages: List[Any]) -> List[Any]:
    clean: List[Any] = []
    pending_tools_allowed = False
    for m in messages:
        if isinstance(m, AIMessage):
            clean.append(m)
            pending_tools_allowed = bool(getattr(m, "tool_calls", None))
        elif isinstance(m, ToolMessage):
            if pending_tools_allowed:
                clean.append(m)
        else:
            clean.append(m)
            pending_tools_allowed = False
    return clean


def call_llm(state: MessagesState):
    # Clean the chat history as you already do
    history = _sanitize_for_llm(state["messages"])

    # Base system prompt
    sys_prompt = SYSTEM_PROMPT

    # If we have a KG message, feed it as background
    kg_msg = get_external_kg_message()
    if kg_msg:
        sys_prompt += (
            "\n\n# Background from Knowledge Graph\n"
            f"{kg_msg}\n\n"
            "Use this as helpful context. Always verify details (especially price/currency) via Saleor GraphQL. "
            "If KG lacks USD or specific currency, fetch actual prices from Saleor."
        )
        try:
            logger.info(f"\n\nSALEOR_TOOL | kg_message_injected | sys_prompt length={len(sys_prompt)}\n\n")
        except Exception:
            pass

    msgs = [SystemMessage(content=sys_prompt)] + history
    ai = llm.invoke(msgs)
    return {"messages": [ai]}


tool_node = ToolNode(TOOLS)


def should_continue(state: MessagesState):
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


graph = StateGraph(MessagesState)
graph.add_node("llm", call_llm)
graph.add_node("tool_exec", tool_node)
graph.add_conditional_edges("llm", should_continue, {"tools": "tool_exec", END: END})
graph.add_edge("tool_exec", "llm")
graph.set_entry_point("llm")
app = graph.compile()

# ---------------------------------
# Convenience helpers for your desired input structure
# ---------------------------------

def make_structured_message(
    users_query: str,
    additional_details: Optional[str] = None,
    kg_products: Optional[Any] = None,
    kg_response: Optional[Any] = None,
) -> HumanMessage:
    """Build a HumanMessage following your desired four-field input."""
    si = StructuredInput(
        users_query=users_query,
        additional_details=additional_details,
        kg_products=kg_products,
        kg_response=kg_response,
    )

    # # Also push a compact KG note into the background channel (optional)
    # if kg_products or kg_response:
    #     try:
    #         combined_msg = "".join([
    #             (kg_response if isinstance(kg_response, str) else json.dumps(kg_response, ensure_ascii=False)) if kg_response is not None else "",
    #             "\n",
    #             (kg_products if isinstance(kg_products, str) else json.dumps(kg_products, ensure_ascii=False)) if kg_products is not None else "",
    #         ]).strip()
    #         if combined_msg:
    #             set_external_kg_context({"message": combined_msg})
    #     except Exception:
    #         pass

    # If kg_products exist, inject explicit JSON instruction
    if kg_products and isinstance(kg_products, list):
        forced_context = (
            f"\n\n# IMPORTANT: You MUST generate ONE GraphQL query using all of these product IDs: {json.dumps(kg_products)}\n"
            "Do not split into multiple queries. Do not drop or reformat IDs."
        )
    else:
        forced_context = ""

    return HumanMessage(content=_render_structured_input(si))


def run_structured(
    users_query: str,
    additional_details: Optional[str] = None,
    kg_products: Optional[Any] = None,
    kg_response: Optional[Any] = None,
    state: Optional[MessagesState] = None,
) -> MessagesState:
    """
    One-call helper that:
      - formats your four input fields
      - invokes the compiled graph
      - returns the updated state
    """
    if state is None:
        state = {"messages": []}
    state["messages"].append(
        make_structured_message(
            users_query=users_query,
            additional_details=additional_details,
            kg_products=kg_products,
            kg_response=kg_response,
        )
    )
    result = app.invoke(state)

    # Runtime validation if kg_products is present
    if kg_products:
        ai_msg = next((m for m in result["messages"] if isinstance(m, AIMessage)), None)
        if ai_msg and ai_msg.tool_calls:
            tool_text = str(ai_msg.tool_calls)
            for pid in kg_products:
                if pid not in tool_text:
                    logger.warning(f"⚠️ Missing product ID {pid} in bulk query")
    return result


# ---------------------------------
# Structured product fetch (deterministic GraphQL)
# ---------------------------------
def fetch_products_structured(ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch product details directly via GraphQL for a list of product IDs and
    return a structured list suitable for deterministic consumption.

    Each item includes: id, name, channel (from CHANNEL_SLUG), price {amount, currency},
    isAvailableForPurchase, isPublished.
    """
    try:
        query = build_bulk_product_query(ids)
        headers = {"Authorization": f"Bearer {SALEOR_TOKEN}"} if SALEOR_TOKEN and SALEOR_TOKEN != "REPLACE_WITH_YOUR_API_TOKEN" else {}
        resp = requests.post(
            SALEOR_ENDPOINT,
            json={
                "query": query,
                "variables": {"ids": ids},
            },
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        data = (payload or {}).get("data") or {}
        products = (((data.get("products") or {}).get("edges") or []))

        results: List[Dict[str, Any]] = []
        for edge in products:
            node = (edge or {}).get("node") or {}
            pid = node.get("id")
            name = node.get("name")
            listings = node.get("channelListings") or []

            price_amount = None
            price_currency = None
            is_available = None
            is_published = None
            chosen_channel = None

            for listing in listings:
                channel = (listing or {}).get("channel") or {}
                if channel.get("slug") == CHANNEL_SLUG:
                    chosen_channel = channel.get("slug")
                    pricing = (listing or {}).get("pricing") or {}
                    price_range = pricing.get("priceRange") or {}
                    start = price_range.get("start") or {}
                    gross = (start.get("gross") or {})
                    price_amount = gross.get("amount")
                    price_currency = gross.get("currency")
                    is_available = listing.get("isAvailableForPurchase")
                    is_published = listing.get("isPublished")
                    break

            if pid:
                results.append({
                    "id": pid,
                    "name": name,
                    "channel": chosen_channel or CHANNEL_SLUG,
                    "price": {"amount": price_amount, "currency": price_currency},
                    "isAvailableForPurchase": is_available,
                    "isPublished": is_published,
                })

        logger.info(f"SALEOR_TOOL | structured_products_fetched | count={len(results)}")
        return results
    except Exception as e:
        try:
            logger.exception(f"SALEOR_TOOL | structured_products_error: {e}")
        except Exception:
            pass
        return []


# ---------------------------------
# Simple structured REPL (optional)
# ---------------------------------
if __name__ == "__main__":
    print("Saleor GraphQL Tool Agent (Simplified Flow) — type 'exit' to quit.\n")
    state: MessagesState = {"messages": []}
    while True:
        uq = input("Users query: ").strip()
        # uq = "can you suggest me some healthy drinks along with there prices."
        if uq.lower() == "exit":
            break
        ad = input("Additional details (optional): ").strip() or None
        kp = input("KG products (optional, JSON or text): ").strip()
        # kp = [["Carrot Juice","Banana Juice", "Bean Juice"]]
        kp_val = None
        if kp:
            try:
                kp_val = json.loads(kp)
            except Exception:
                kp_val = kp
        kr = input("KG response (optional, JSON or text): ").strip()
        # kr = [ "Here are some healthy drink options based on the provided context:\n\n1. **Carrot Juice**: Made from 100% pure, squeezed carrots, it offers the sweet, orange nectar of Mother Earth and helps improve eyesight naturally.\n2. **Banana Juice**: An exotic drink made from ripe bananas, packed with natural protein and the goodness of the tropical sun.\n3. **Bean Juice**: A health-conscious energy drink made from beans, prepared from allotment to bottle in under 8 hours.\n\nLet me know if you'd like more details about any of these!"]
        kr_val = None
        if kr:
            try:
                kr_val = json.loads(kr)
            except Exception:
                kr_val = kr

        state = run_structured(uq, ad, kp_val, kr_val, state)
        ai = next(m for m in reversed(state["messages"]) if isinstance(m, AIMessage))
        print("\nAssistant:\n", ai.content, "\n")
