/* eslint-disable */
import * as types from './graphql';



/**
 * Map of all GraphQL operations in the project.
 *
 * This map has several performance disadvantages:
 * 1. It is not tree-shakeable, so it will include all operations in the project.
 * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
 * 3. It does not support dead code elimination, so it will add unused operations.
 *
 * Therefore it is highly recommended to use the babel or swc plugin for production.
 */
const documents = {
    "query ChannelsList {\n  channels {\n    id\n    name\n    slug\n    isActive\n    currencyCode\n    countries {\n      country\n      code\n    }\n  }\n}": types.ChannelsListDocument,
    "mutation CheckoutAddLine($id: ID!, $productVariantId: ID!) {\n  checkoutLinesAdd(id: $id, lines: [{quantity: 1, variantId: $productVariantId}]) {\n    checkout {\n      id\n      lines {\n        id\n        quantity\n        variant {\n          name\n          product {\n            name\n          }\n        }\n      }\n    }\n    errors {\n      message\n    }\n  }\n}": types.CheckoutAddLineDocument,
    "mutation CheckoutCreate($channel: String!) {\n  checkoutCreate(input: {channel: $channel, lines: []}) {\n    checkout {\n      id\n      email\n      lines {\n        id\n        quantity\n        totalPrice {\n          gross {\n            amount\n            currency\n          }\n        }\n        variant {\n          product {\n            id\n            name\n            slug\n            thumbnail {\n              url\n              alt\n            }\n            category {\n              name\n            }\n          }\n          pricing {\n            price {\n              gross {\n                amount\n                currency\n              }\n            }\n          }\n          name\n          id\n        }\n      }\n      totalPrice {\n        gross {\n          amount\n          currency\n        }\n      }\n    }\n    errors {\n      field\n      code\n    }\n  }\n}": types.CheckoutCreateDocument,
    "mutation CheckoutDeleteLines($checkoutId: ID!, $lineIds: [ID!]!) {\n  checkoutLinesDelete(id: $checkoutId, linesIds: $lineIds) {\n    checkout {\n      id\n    }\n    errors {\n      field\n      code\n    }\n  }\n}": types.CheckoutDeleteLinesDocument,
    "query CheckoutFind($id: ID!) {\n  checkout(id: $id) {\n    id\n    email\n    lines {\n      id\n      quantity\n      totalPrice {\n        gross {\n          amount\n          currency\n        }\n      }\n      variant {\n        product {\n          id\n          name\n          slug\n          thumbnail {\n            url\n            alt\n          }\n          category {\n            name\n          }\n        }\n        pricing {\n          price {\n            gross {\n              amount\n              currency\n            }\n          }\n        }\n        name\n        id\n      }\n    }\n    totalPrice {\n      gross {\n        amount\n        currency\n      }\n    }\n  }\n}": types.CheckoutFindDocument,
    "query CurrentUser {\n  me {\n    ...UserDetails\n  }\n}": types.CurrentUserDocument,
    "query CurrentUserOrderList {\n  me {\n    ...UserDetails\n    orders(first: 10) {\n      edges {\n        node {\n          ...OrderDetails\n        }\n      }\n    }\n  }\n}": types.CurrentUserOrderListDocument,
    "fragment MenuItem on MenuItem {\n  id\n  name\n  level\n  category {\n    id\n    slug\n    name\n  }\n  collection {\n    id\n    name\n    slug\n  }\n  page {\n    id\n    title\n    slug\n  }\n  url\n}\n\nquery MenuGetBySlug($slug: String!, $channel: String!) {\n  menu(slug: $slug, channel: $channel) {\n    items {\n      ...MenuItem\n      children {\n        ...MenuItem\n      }\n    }\n  }\n}": types.MenuItemFragmentDoc,
    "fragment OrderDetails on Order {\n  id\n  number\n  created\n  total {\n    gross {\n      amount\n      currency\n    }\n  }\n  lines {\n    variant {\n      id\n      name\n      product {\n        id\n        name\n        description\n        slug\n        thumbnail {\n          url\n          alt\n        }\n        category {\n          id\n          name\n        }\n      }\n      pricing {\n        price {\n          gross {\n            amount\n            currency\n          }\n        }\n      }\n    }\n    quantity\n  }\n  paymentStatus\n}": types.OrderDetailsFragmentDoc,
    "query PageGetBySlug($slug: String!) {\n  page(slug: $slug) {\n    id\n    slug\n    title\n    seoTitle\n    seoDescription\n    content\n  }\n}": types.PageGetBySlugDocument,
    "query ProductDetails($slug: String!, $channel: String!) {\n  product(slug: $slug, channel: $channel) {\n    id\n    name\n    slug\n    description\n    seoTitle\n    seoDescription\n    thumbnail(size: 1024, format: WEBP) {\n      url\n      alt\n    }\n    category {\n      id\n      name\n    }\n    variants {\n      ...VariantDetails\n    }\n    pricing {\n      priceRange {\n        start {\n          gross {\n            amount\n            currency\n          }\n        }\n        stop {\n          gross {\n            amount\n            currency\n          }\n        }\n      }\n    }\n  }\n}": types.ProductDetailsDocument,
    "query ProductList($first: Int = 9, $channel: String!) {\n  products(first: $first, channel: $channel) {\n    edges {\n      node {\n        ...ProductListItem\n      }\n    }\n  }\n}": types.ProductListDocument,
    "query ProductListByCategory($slug: String!, $channel: String!) {\n  category(slug: $slug) {\n    name\n    description\n    seoDescription\n    seoTitle\n    products(first: 100, channel: $channel) {\n      edges {\n        node {\n          ...ProductListItem\n        }\n      }\n    }\n  }\n}": types.ProductListByCategoryDocument,
    "query ProductListByCollection($slug: String!, $channel: String!) {\n  collection(slug: $slug, channel: $channel) {\n    name\n    description\n    seoDescription\n    seoTitle\n    products(first: 100) {\n      edges {\n        node {\n          ...ProductListItem\n        }\n      }\n    }\n  }\n}": types.ProductListByCollectionDocument,
    "fragment ProductListItem on Product {\n  id\n  name\n  slug\n  pricing {\n    priceRange {\n      start {\n        gross {\n          amount\n          currency\n        }\n      }\n      stop {\n        gross {\n          amount\n          currency\n        }\n      }\n    }\n  }\n  category {\n    id\n    name\n  }\n  thumbnail(size: 1024, format: WEBP) {\n    url\n    alt\n  }\n}": types.ProductListItemFragmentDoc,
    "query ProductListPaginated($first: Int!, $after: String, $channel: String!, $sortBy: ProductOrder) {\n  products(first: $first, after: $after, channel: $channel, sortBy: $sortBy) {\n    totalCount\n    edges {\n      node {\n        ...ProductListItem\n      }\n      cursor\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}": types.ProductListPaginatedDocument,
    "query SearchProducts($search: String!, $sortBy: ProductOrderField!, $sortDirection: OrderDirection!, $first: Int!, $after: String, $channel: String!) {\n  products(\n    first: $first\n    after: $after\n    channel: $channel\n    sortBy: {field: $sortBy, direction: $sortDirection}\n    filter: {search: $search}\n  ) {\n    totalCount\n    edges {\n      node {\n        ...ProductListItem\n      }\n      cursor\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}": types.SearchProductsDocument,
    "fragment UserDetails on User {\n  id\n  email\n  firstName\n  lastName\n  avatar {\n    url\n    alt\n  }\n}": types.UserDetailsFragmentDoc,
    "fragment VariantDetails on ProductVariant {\n  id\n  name\n  quantityAvailable\n  pricing {\n    price {\n      gross {\n        currency\n        amount\n      }\n    }\n  }\n}": types.VariantDetailsFragmentDoc,
};

/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query ChannelsList {\n  channels {\n    id\n    name\n    slug\n    isActive\n    currencyCode\n    countries {\n      country\n      code\n    }\n  }\n}"): typeof import('./graphql').ChannelsListDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "mutation CheckoutAddLine($id: ID!, $productVariantId: ID!) {\n  checkoutLinesAdd(id: $id, lines: [{quantity: 1, variantId: $productVariantId}]) {\n    checkout {\n      id\n      lines {\n        id\n        quantity\n        variant {\n          name\n          product {\n            name\n          }\n        }\n      }\n    }\n    errors {\n      message\n    }\n  }\n}"): typeof import('./graphql').CheckoutAddLineDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "mutation CheckoutCreate($channel: String!) {\n  checkoutCreate(input: {channel: $channel, lines: []}) {\n    checkout {\n      id\n      email\n      lines {\n        id\n        quantity\n        totalPrice {\n          gross {\n            amount\n            currency\n          }\n        }\n        variant {\n          product {\n            id\n            name\n            slug\n            thumbnail {\n              url\n              alt\n            }\n            category {\n              name\n            }\n          }\n          pricing {\n            price {\n              gross {\n                amount\n                currency\n              }\n            }\n          }\n          name\n          id\n        }\n      }\n      totalPrice {\n        gross {\n          amount\n          currency\n        }\n      }\n    }\n    errors {\n      field\n      code\n    }\n  }\n}"): typeof import('./graphql').CheckoutCreateDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "mutation CheckoutDeleteLines($checkoutId: ID!, $lineIds: [ID!]!) {\n  checkoutLinesDelete(id: $checkoutId, linesIds: $lineIds) {\n    checkout {\n      id\n    }\n    errors {\n      field\n      code\n    }\n  }\n}"): typeof import('./graphql').CheckoutDeleteLinesDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query CheckoutFind($id: ID!) {\n  checkout(id: $id) {\n    id\n    email\n    lines {\n      id\n      quantity\n      totalPrice {\n        gross {\n          amount\n          currency\n        }\n      }\n      variant {\n        product {\n          id\n          name\n          slug\n          thumbnail {\n            url\n            alt\n          }\n          category {\n            name\n          }\n        }\n        pricing {\n          price {\n            gross {\n              amount\n              currency\n            }\n          }\n        }\n        name\n        id\n      }\n    }\n    totalPrice {\n      gross {\n        amount\n        currency\n      }\n    }\n  }\n}"): typeof import('./graphql').CheckoutFindDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query CurrentUser {\n  me {\n    ...UserDetails\n  }\n}"): typeof import('./graphql').CurrentUserDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query CurrentUserOrderList {\n  me {\n    ...UserDetails\n    orders(first: 10) {\n      edges {\n        node {\n          ...OrderDetails\n        }\n      }\n    }\n  }\n}"): typeof import('./graphql').CurrentUserOrderListDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "fragment MenuItem on MenuItem {\n  id\n  name\n  level\n  category {\n    id\n    slug\n    name\n  }\n  collection {\n    id\n    name\n    slug\n  }\n  page {\n    id\n    title\n    slug\n  }\n  url\n}\n\nquery MenuGetBySlug($slug: String!, $channel: String!) {\n  menu(slug: $slug, channel: $channel) {\n    items {\n      ...MenuItem\n      children {\n        ...MenuItem\n      }\n    }\n  }\n}"): typeof import('./graphql').MenuItemFragmentDoc;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "fragment OrderDetails on Order {\n  id\n  number\n  created\n  total {\n    gross {\n      amount\n      currency\n    }\n  }\n  lines {\n    variant {\n      id\n      name\n      product {\n        id\n        name\n        description\n        slug\n        thumbnail {\n          url\n          alt\n        }\n        category {\n          id\n          name\n        }\n      }\n      pricing {\n        price {\n          gross {\n            amount\n            currency\n          }\n        }\n      }\n    }\n    quantity\n  }\n  paymentStatus\n}"): typeof import('./graphql').OrderDetailsFragmentDoc;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query PageGetBySlug($slug: String!) {\n  page(slug: $slug) {\n    id\n    slug\n    title\n    seoTitle\n    seoDescription\n    content\n  }\n}"): typeof import('./graphql').PageGetBySlugDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query ProductDetails($slug: String!, $channel: String!) {\n  product(slug: $slug, channel: $channel) {\n    id\n    name\n    slug\n    description\n    seoTitle\n    seoDescription\n    thumbnail(size: 1024, format: WEBP) {\n      url\n      alt\n    }\n    category {\n      id\n      name\n    }\n    variants {\n      ...VariantDetails\n    }\n    pricing {\n      priceRange {\n        start {\n          gross {\n            amount\n            currency\n          }\n        }\n        stop {\n          gross {\n            amount\n            currency\n          }\n        }\n      }\n    }\n  }\n}"): typeof import('./graphql').ProductDetailsDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query ProductList($first: Int = 9, $channel: String!) {\n  products(first: $first, channel: $channel) {\n    edges {\n      node {\n        ...ProductListItem\n      }\n    }\n  }\n}"): typeof import('./graphql').ProductListDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query ProductListByCategory($slug: String!, $channel: String!) {\n  category(slug: $slug) {\n    name\n    description\n    seoDescription\n    seoTitle\n    products(first: 100, channel: $channel) {\n      edges {\n        node {\n          ...ProductListItem\n        }\n      }\n    }\n  }\n}"): typeof import('./graphql').ProductListByCategoryDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query ProductListByCollection($slug: String!, $channel: String!) {\n  collection(slug: $slug, channel: $channel) {\n    name\n    description\n    seoDescription\n    seoTitle\n    products(first: 100) {\n      edges {\n        node {\n          ...ProductListItem\n        }\n      }\n    }\n  }\n}"): typeof import('./graphql').ProductListByCollectionDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "fragment ProductListItem on Product {\n  id\n  name\n  slug\n  pricing {\n    priceRange {\n      start {\n        gross {\n          amount\n          currency\n        }\n      }\n      stop {\n        gross {\n          amount\n          currency\n        }\n      }\n    }\n  }\n  category {\n    id\n    name\n  }\n  thumbnail(size: 1024, format: WEBP) {\n    url\n    alt\n  }\n}"): typeof import('./graphql').ProductListItemFragmentDoc;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query ProductListPaginated($first: Int!, $after: String, $channel: String!, $sortBy: ProductOrder) {\n  products(first: $first, after: $after, channel: $channel, sortBy: $sortBy) {\n    totalCount\n    edges {\n      node {\n        ...ProductListItem\n      }\n      cursor\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}"): typeof import('./graphql').ProductListPaginatedDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query SearchProducts($search: String!, $sortBy: ProductOrderField!, $sortDirection: OrderDirection!, $first: Int!, $after: String, $channel: String!) {\n  products(\n    first: $first\n    after: $after\n    channel: $channel\n    sortBy: {field: $sortBy, direction: $sortDirection}\n    filter: {search: $search}\n  ) {\n    totalCount\n    edges {\n      node {\n        ...ProductListItem\n      }\n      cursor\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n    }\n  }\n}"): typeof import('./graphql').SearchProductsDocument;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "fragment UserDetails on User {\n  id\n  email\n  firstName\n  lastName\n  avatar {\n    url\n    alt\n  }\n}"): typeof import('./graphql').UserDetailsFragmentDoc;
/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "fragment VariantDetails on ProductVariant {\n  id\n  name\n  quantityAvailable\n  pricing {\n    price {\n      gross {\n        currency\n        amount\n      }\n    }\n  }\n}"): typeof import('./graphql').VariantDetailsFragmentDoc;


export function graphql(source: string) {
  return (documents as any)[source] ?? {};
}
