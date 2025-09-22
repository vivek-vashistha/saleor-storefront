import Hero from "./Hero";
import RewardsBar from "./RewardsBar";
import FeaturedProducts from "./FeaturedProducts";
import { ProductListByCollectionDocument } from "@/gql/graphql";
import { executeGraphQL } from "@/lib/graphql";
import { ProductList } from "@/ui/components/ProductList";

export const metadata = {
	title: "iHerb | Vitamins, Supplements, Natural Health Products",
	description:
		"Storefront Next.js Example for building performant e-commerce experiences with Saleor - the composable, headless commerce platform for global brands.",
};

export default async function Page(props: { params: Promise<{ channel: string }> }) {
	const params = await props.params;
	const data = await executeGraphQL(ProductListByCollectionDocument, {
		variables: {
			slug: "featured-products",
			channel: params.channel,
		},
		revalidate: 60,
	});

	if (!data.collection?.products) {
		return null;
	}

	const products = data.collection?.products.edges.map(({ node: product }) => product);

	return (
		<>
			{/* <div className="mx-auto max-w-7xl p-4 mb-4 text-center rounded border bg-yellow-50 text-yellow-900">
				this is the banner
			</div> */}
			<Hero />
			<RewardsBar />
			<FeaturedProducts />
			<section className="mx-auto max-w-7xl p-8 pb-16">
				<h2 className="sr-only">Product list</h2>
				<ProductList products={products} />
			</section>
		</>
	);
}
