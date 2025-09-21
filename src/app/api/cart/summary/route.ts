import { NextRequest, NextResponse } from "next/server";
import * as Checkout from "@/lib/checkout";

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const channel = url.searchParams.get("channel") || "default-channel";

    const checkoutId = await Checkout.getIdFromCookies(channel);
    if (!checkoutId) {
      console.log("/api/cart/summary no checkout", { channel });
      return NextResponse.json({ checkoutId: null, items: [], lineCount: 0 }, { status: 200 });
    }

    const checkout = await Checkout.find(checkoutId);

    const items = (checkout?.lines || []).map((line) => ({
      id: line?.id ?? null,
      quantity: line?.quantity ?? 0,
      productName: line?.variant?.product?.name ?? "",
      productSlug: line?.variant?.product?.slug ?? "",
      variantId: line?.variant?.id ?? "",
      variantName: line?.variant?.name ?? "",
      currency: line?.totalPrice?.gross?.currency ?? checkout?.totalPrice?.gross?.currency ?? "USD",
      unitPrice: line?.unitPrice?.gross?.amount ?? 0,
      totalPrice: line?.totalPrice?.gross?.amount ?? 0,
      image: line?.variant?.product?.thumbnail?.url ?? null,
    }));

    const lineCount = items.reduce((acc, it) => acc + (it.quantity || 0), 0);
    const currency = checkout?.totalPrice?.gross?.currency || items[0]?.currency || "USD";
    try {
      console.log(
        "/api/cart/summary resp",
        JSON.stringify({
          channel,
          checkoutId,
          lineCount,
          items: items.map((it) => ({ name: it.productName, qty: it.quantity })),
        })
      );
    } catch {}

    return NextResponse.json({ checkoutId, items, lineCount, currency }, { status: 200 });
  } catch (error) {
    console.error("/api/cart/summary error", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
