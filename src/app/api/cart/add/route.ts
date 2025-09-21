import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";
import { executeGraphQL } from "@/lib/graphql";
import * as Checkout from "@/lib/checkout";
import { CheckoutAddLineDocument, ProductDetailsDocument, SearchProductsDocument, ProductOrderField, OrderDirection } from "@/gql/graphql";

function sanitizeName(name: string): string {
    // Normalize apostrophes and remove common symbols/encoding artifacts/punctuation noise
    let normalized = name
        .replace(/[’']/g, "'")
        .replace(/[®™]/g, "")
        .replace(/Â/g, "")
        // Remove anything in parentheses which often contains dosage/pack info
        .replace(/\([^)]*\)/g, "")
        // Replace commas and other punctuation with spaces
        .replace(/[,:;|]/g, " ");

    // Remove common gender suffix anywhere in the string
    normalized = normalized.replace(/\s*-\s*(Men's|Womens|Women's|Mens)\b/gi, "");

    // Collapse extra whitespace
    normalized = normalized.replace(/\s+/g, " ").trim();
    return normalized;
}

function buildSearchVariants(raw: string, sanitized: string): string[] {
    const variants: string[] = [];
    const add = (s?: string) => { const v = (s || "").trim(); if (v) variants.push(v); };

    // Start with raw and sanitized
    add(raw);
    add(sanitized);

    // Remove parentheses variants
    const noParenRaw = raw.replace(/\([^)]*\)/g, "").replace(/\s+/g, " "); add(noParenRaw);
    const noParenSan = sanitized.replace(/\([^)]*\)/g, "").replace(/\s+/g, " "); add(noParenSan);

    // No punctuation variant
    const noPunct = noParenSan.replace(/[^a-z0-9\s]/gi, " ").replace(/\s+/g, " "); add(noPunct);

    // Token-based queries
    const tokens = noPunct
        .split(/\s+/)
        .map((t) => t.trim())
        .filter((t) => t.length >= 2);
    if (tokens.length) {
        const top = tokens.slice(0, 6).join(" ");
        add(top);

        // Try brand + keyword if detectable
        // Heuristic: brand is text before first comma in raw
        const brand = (raw.split(",")[0] || tokens[0] || "").trim();
        const keywords = [
            "probiotic",
            "probiotics",
            "magnesium",
            "melatonin",
            "collagen",
            "vitamin",
            "b12",
            "coq10",
            "creatine",
            "capsules",
            "caps",
            "powder",
            "gummies",
        ];
        const primary = tokens.find((t) => keywords.includes(t.toLowerCase())) || "";
        if (brand) {
            add(brand);
            if (primary) add(`${brand} ${primary}`);
        }
    }

    // Comma-separated parts from raw (e.g., brand, specific line, pack info)
    raw.split(",").map((s) => s.trim()).forEach((part) => add(part));

    // De-duplicate while preserving order
    return Array.from(new Set(variants));
}

function slugify(input: string): string {
    return input
        .toLowerCase()
        .normalize("NFKD")
        .replace(/[’']/g, "")
        .replace(/[®™]/g, "")
        .replace(/Â/g, "")
        // Keep measurement info from parentheses by turning parens into spaces
        .replace(/[()]/g, " ")
        .replace(/&/g, " and ")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "");
}

function buildSlugCandidates(raw: string, sanitized: string): string[] {
    const candidates: string[] = [];
    const add = (s?: string) => { const v = (s || "").trim(); if (v) candidates.push(slugify(v)); };

    add(raw);
    add(sanitized);
    add(raw.replace(/\([^)]*\)/g, ""));
    add(sanitized.replace(/\([^)]*\)/g, ""));

    // comma parts often include brand and product line
    raw.split(",").forEach((p) => add(p));

    // Brand + primary keyword
    const brand = (raw.split(",")[0] || "").trim();
    const primaryKeywords = [
        "probiotic",
        "probiotics",
        "magnesium",
        "melatonin",
        "collagen",
        "vitamin",
        "b12",
        "coq10",
        "creatine",
        "capsules",
        "caps",
        "powder",
        "gummies",
    ];
    const tokens = sanitized.replace(/[^a-z0-9\s]/gi, " ").split(/\s+/).filter(Boolean);
    const primary = tokens.find((t) => primaryKeywords.includes(t.toLowerCase()));
    if (brand) add(brand);
    if (brand && primary) add(`${brand} ${primary}`);

    return Array.from(new Set(candidates));
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
        const primary = nodes.filter((p) => p.name.toLowerCase().includes(query.toLowerCase()));
        const loosen = (s: string) => s
            .toLowerCase()
            .replace(/men's|mens|women's|womens/gi, "")
            .replace(/[^a-z0-9\s]/gi, "")
            .trim();
        const target = loosen(query);
        const primarySlugs = new Set(primary.map((p) => p.slug));
        const secondary = nodes.filter(
            (p) => !primarySlugs.has(p.slug) && (loosen(p.name) === target || loosen(p.name).includes(target))
        );
        const secondarySlugs = new Set(secondary.map((p) => p.slug));
        const others = nodes.filter((p) => !primarySlugs.has(p.slug) && !secondarySlugs.has(p.slug));
        let candidates: Array<{ name: string; slug: string }> = [...primary, ...secondary, ...others].slice(0, 10);

        if (candidates.length === 0) {
            console.warn("/api/cart/add no match — trying fallback search variants", { query });
            const variants = buildSearchVariants(name, query);
            for (const v of variants) {
                if (!v) continue;
                const retryVars = { ...searchVars, search: v } as const;
                const retryResp = await executeGraphQL(SearchProductsDocument, {
                    variables: retryVars,
                    cache: "no-cache",
                    withAuth: false,
                });
                const retryEdges = (retryResp.products?.edges ?? []) as any[];
                if (retryEdges.length > 0) {
                    const retryNodes: Array<{ name: string; slug: string }> = retryEdges.map((e: any) => ({
                        name: e?.node?.name as string,
                        slug: e?.node?.slug as string,
                    }));
                    const retryPrimary = retryNodes.filter((p) => p.name.toLowerCase().includes(query.toLowerCase()));
                    const retryPrimarySlugs = new Set(retryPrimary.map((p) => p.slug));
                    const retrySecondary = retryNodes.filter((p) => !retryPrimarySlugs.has(p.slug));
                    candidates = [...retryPrimary, ...retrySecondary].slice(0, 10);
                    console.log("/api/cart/add recovered candidates via variant", { variant: v, count: candidates.length });
                    break;
                }
            }
            if (candidates.length === 0) {
                // Try slug-based lookup as a last resort: some Saleor setups match slugs better than name search
                console.warn("/api/cart/add still no match — trying slug candidates", { query });
                const slugCandidates = buildSlugCandidates(name, query);
                for (const s of slugCandidates) {
                    try {
                        const det = await executeGraphQL(ProductDetailsDocument, {
                            variables: { slug: s, channel },
                            cache: "no-cache",
                            withAuth: false,
                        });
                        if (det.product?.slug) {
                            candidates = [{ name: det.product.name, slug: det.product.slug }];
                            console.log("/api/cart/add recovered via slug", { slug: det.product.slug });
                            break;
                        }
                    } catch {}
                }
                if (candidates.length === 0) {
                    // As a very last resort, try the last token as a potential slug tail
                    const tokens = query.replace(/[^a-z0-9\s]/gi, " ").split(/\s+/).filter(Boolean);
                    const tail = tokens[tokens.length - 1];
                    if (tail) {
                        const guess = slugify(tail);
                        try {
                            const det = await executeGraphQL(ProductDetailsDocument, {
                                variables: { slug: guess, channel },
                                cache: "no-cache",
                                withAuth: false,
                            });
                            if (det.product?.slug) {
                                candidates = [{ name: det.product.name, slug: det.product.slug }];
                                console.log("/api/cart/add recovered via tail slug", { slug: det.product.slug });
                            }
                        } catch {}
                    }
                    if (candidates.length === 0) {
                        return NextResponse.json({ error: "No matching product found" }, { status: 404 });
                    }
                }
            }
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


