import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";
import { executeGraphQL } from "@/lib/graphql";
import * as Checkout from "@/lib/checkout";
import { CheckoutAddLineDocument, ProductDetailsDocument, SearchProductsDocument, ProductOrderField, OrderDirection } from "@/gql/graphql";

function sanitizeName(name: string): string {
    // Normalize apostrophes and remove common gender suffix anywhere in the string
    // e.g. " - Men's" / "- Womens" / "- Women's" / "- Mens"
    const normalized = name.replace(/[’']/g, "'");
    return normalized.replace(/\s*-\s*(Men's|Womens|Women's|Mens)\b/gi, "").trim();
}

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { name, channel } = body as { name?: string; channel?: string };

        if (!name || !channel) {
            console.error("/api/cart/add missing params", { name, channel });
            return NextResponse.json({ error: "Missing name or channel" }, { status: 400 });
        }

        const query = sanitizeName(name);
        // Log request basics and cookie names (avoid logging sensitive cookie values)
        const cookieNames = req.cookies.getAll().map((c) => c.name);
        console.log("/api/cart/add query", { original: name, sanitized: query, channel, cookieNames });

        // Use the same search query our app uses for searching products
        const searchVars = {
            search: query,
            sortBy: ProductOrderField.Name,
            sortDirection: OrderDirection.Asc,
            first: 100,
            channel,
        } as const;
        console.log("/api/cart/add searchVars", searchVars);
        const searchResp = await executeGraphQL(SearchProductsDocument, {
            variables: searchVars,
            cache: "no-cache",
            withAuth: false,
        });

        console.log("/api/cart/add searchResp", searchResp);

        const edgesRaw = searchResp.products?.edges ?? [];
        // Helpful debug: list names/slugs of candidates
        try {
            const nodesDbg = (edgesRaw as any[]).map((e: any) => ({ name: e?.node?.name, slug: e?.node?.slug }));
            console.log("/api/cart/add edges nodes", nodesDbg);
        } catch {}
        // Full dump (formatted). Beware of large output in prod logs.
        try {
            console.log(
                "/api/cart/add edges raw",
                JSON.stringify(edgesRaw, null, 2)
            );
        } catch {}
        // Build candidate list: strongest name-includes first, then others
        const nodes: Array<{ name: string; slug: string }> = (edgesRaw as any[]).map((e: any) => ({
            name: e?.node?.name as string,
            slug: e?.node?.slug as string,
        }));
        const primary = nodes.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));
        const loosen = (s: string) => s
            .toLowerCase()
            .replace(/men's|mens|women's|womens/gi, "")
            .replace(/[^a-z0-9\s]/gi, "")
            .trim();
        const target = loosen(query);
        const secondary = nodes.filter(p => !primary.includes(p) && (loosen(p.name) === target || loosen(p.name).includes(target)));
        const others = nodes.filter(p => !primary.includes(p) && !secondary.includes(p));
        const candidates = [...primary, ...secondary, ...others].slice(0, 10);

        if (candidates.length === 0) {
            console.warn("/api/cart/add no match", { query });
            return NextResponse.json({ error: "No matching product found" }, { status: 404 });
        }

        // Iterate candidates to find first with in-stock variant
        let picked: { slug: string; variantId: string } | null = null;
        let lastTriedSlug: string | undefined;
        for (const c of candidates) {
            console.log("/api/cart/add candidate", { slug: c.slug, name: c.name });
            lastTriedSlug = c.slug;
            const det = await executeGraphQL(ProductDetailsDocument, {
                variables: { slug: c.slug, channel },
                cache: "no-cache",
                withAuth: false,
            });
            const prod = det.product;
            const vars = prod?.variants || [];
            // Log variants availability snapshot for this candidate
            try {
                console.log(
                    "/api/cart/add candidate variants",
                    (vars as any[]).map((v: any) => ({ id: v?.id, name: v?.name, quantityAvailable: v?.quantityAvailable }))
                );
            } catch {}
            const inStockVar = vars.find(v => (v?.quantityAvailable ?? 0) > 0);
            if (inStockVar?.id) {
                picked = { slug: prod!.slug, variantId: inStockVar.id };
                break;
            }
        }

        if (!picked) {
            // Fallback: re-run a looser search with trimmed tokens
            const tokens = query
                .split(/\s+/)
                .map((t) => t.replace(/[^a-z0-9-]/gi, ""))
                .filter((t) => t.length >= 3)
                .filter((t) => !["mens", "men", "womens", "women", "mid", "gtx", "gore-tex", "boots", "boot", "hiking", "waterproof"].includes(t.toLowerCase()));
            const loose = tokens.slice(0, 3).join(" ");
            console.warn("/api/cart/add retry loose search", { loose });
            if (loose) {
                const retryVars = { ...searchVars, search: loose } as const;
                const retryResp = await executeGraphQL(SearchProductsDocument, {
                    variables: retryVars,
                    cache: "no-cache",
                    withAuth: false,
                });
                const retryEdges = (retryResp.products?.edges ?? []) as any[];
                for (const e of retryEdges) {
                    const slug = e?.node?.slug as string | undefined;
                    const name = e?.node?.name as string | undefined;
                    if (!slug) continue;
                    console.log("/api/cart/add retry candidate", { slug, name });
                    const det = await executeGraphQL(ProductDetailsDocument, {
                        variables: { slug, channel },
                        cache: "no-cache",
                        withAuth: false,
                    });
                    const vars = det.product?.variants || [];
                    const inStockVar = vars.find((v: any) => (v?.quantityAvailable ?? 0) > 0);
                    if (inStockVar?.id) {
                        picked = { slug, variantId: inStockVar.id };
                        break;
                    }
                }
            }
            if (!picked) {
            console.warn("/api/cart/add all candidates OOS", { query, loose, lastTriedSlug });
            return NextResponse.json({ error: "All variants out of stock", slug: lastTriedSlug }, { status: 409 });
            }
        }
        console.log("/api/cart/add picked", picked);

        // Ensure checkout exists and is stored in cookies
        const prevCheckoutId = await Checkout.getIdFromCookies(channel);
        console.log("/api/cart/add prevCheckoutId", { prevCheckoutId });
        const checkout = await Checkout.findOrCreate({
            checkoutId: prevCheckoutId,
            channel,
        });
        if (!checkout) {
            console.error("/api/cart/add failed to get checkout");
            return NextResponse.json({ error: "Failed to create checkout" }, { status: 500 });
        }
        await Checkout.saveIdToCookie(channel, checkout.id);
        console.log("/api/cart/add checkout", { checkoutId: checkout.id, wasCreated: !prevCheckoutId || prevCheckoutId !== checkout.id });

        // Add line to checkout
        const addVars = { id: checkout.id, productVariantId: picked.variantId } as const;
        console.log("/api/cart/add addVars", addVars);
        const addResp = await executeGraphQL(CheckoutAddLineDocument, {
            variables: addVars,
            cache: "no-cache",
        });

        if (addResp.checkoutLinesAdd?.errors?.length) {
            console.warn("/api/cart/add mutation errors", addResp.checkoutLinesAdd.errors);
            return NextResponse.json({ success: false, errors: addResp.checkoutLinesAdd.errors }, { status: 409 });
        }

        const updated = addResp.checkoutLinesAdd?.checkout;
        const lineCount = updated?.lines?.reduce((acc, l) => acc + (l?.quantity || 0), 0) || 0;
        try {
            console.log(
                "/api/cart/add updated checkout",
                JSON.stringify({
                    id: updated?.id,
                    lines: (updated?.lines || []).map((l: any) => ({ id: l?.id, qty: l?.quantity, variant: l?.variant?.id })),
                    lineCount,
                }, null, 2)
            );
        } catch {}

        // Revalidate cart route so SSR cart reflects latest checkout
        try {
            revalidatePath(`/${channel}/cart`);
        } catch {}

        return NextResponse.json({ success: true, lineCount, product: { slug: picked.slug }, variantId: picked.variantId, checkoutId: checkout.id });
    } catch (error) {
        console.error("/api/cart/add error", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}


