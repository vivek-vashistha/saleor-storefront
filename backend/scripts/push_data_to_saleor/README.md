# Saleor Data Import Script

This script helps you import product data and images into Saleor.

## Prerequisites

- Node.js installed
- Python installed
- Saleor backend running
- Python dependencies installed (`pip install requests python-dotenv`)

> Note: Before running the import, delete all files inside the `cache/` folder (path: `backend/scripts/push_data_to_saleor/cache/`).

## (Optional) Clear caches before import

The importer uses on-disk caches to reduce API calls. If you're changing data sources or Saleor environments, clear caches first.

## Step 1: Download Images

1. Navigate to the images directory:

   ```bash
   cd images
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Prepare your `images.csv` file with exactly 2 columns:

   - `url` - Image URL
   - `filename` - Local filename for the image

   **Example images.csv data:**

   <div style="overflow-x: auto;">

   | url                                                                                              | filename  |
   | ------------------------------------------------------------------------------------------------ | --------- |
   | https://cloudinary.images-iherb.com/image/upload/f_auto,q_auto:eco/images/now/now02931/g/27.jpg  | 64465.jpg |
   | https://cloudinary.images-iherb.com/image/upload/f_auto,q_auto:eco/images/lkn/lkn01422/g/113.jpg | 95327.jpg |
   | https://cloudinary.images-iherb.com/image/upload/f_auto,q_auto:eco/images/jrw/jrw03020/g/112.jpg | 124.jpg   |
   | https://cloudinary.images-iherb.com/image/upload/f_auto,q_auto:eco/images/jrw/jrw03001/g/15.jpg  | 40594.jpg |
   | https://cloudinary.images-iherb.com/image/upload/f_auto,q_auto:eco/images/cgn/cgn01053/g/169.jpg | 69435.jpg |

   </div>

4. Run the image download script:

   ```bash
   node run_and_save.js
   ```

5. Go back to the main directory:
   ```bash
   cd ..
   ```

## Step 2: Import Products

1. **Configure Environment Variables:**

   Copy the example environment file and update it with your Saleor configuration:

   ```bash
   cp env.example .env
   ```

   Edit `.env` file with your settings:

   ```env
   # Saleor Configuration
   SALEOR_ENDPOINT=https://your-saleor.com/graphql/
   SALEOR_TOKEN=your_staff_api_token_here
   CHANNEL_SLUG=default-channel

   # Processing Configuration
   START_ROW=1
   TOTAL_RECORDS=0
   SKIP_HEADER=true

   # Results CSV (optional)
   # Path to write the output CSV containing created Saleor IDs.
   # Defaults to ../../data/gear/saleor_import_results.csv in repo layout.
   OUTPUT_RESULTS_CSV=../../data/iherb/iherb_product_data - for_Neo4j_push_v3_with_saleor_ID.csv
   ```

2. **Prepare your product data CSV file** in the `backend/data/` directory. The importer supports two schemas:

   ### A) Legacy Gear CSV schema (example: `saleor_products_ready_enriched.csv`)

   **Required columns:**

   - `name` - Product name
   - `slug` - Product slug
   - `description_text` - Product description
   - `category_slug` - Category slug
   - `category_name` - Category name
   - `product_type_slug` - Product type slug
   - `product_type_name` - Product type name
   - `collections` - Collections (comma-separated)
   - `attributes` - Product attributes
   - `rating` - Product rating
   - `tax_class` - Tax class
   - `weight` - Product weight
   - `price` - Product price
   - `image_url` - Image URL
   - `brand` - Brand name
   - `capacity` - Product capacity
   - `weight_attr` - Weight attribute

   **Example CSV data:**

   <div style="overflow-x: auto;">

   | name                            | slug                            | description_text                                                  | category_slug | category_name | product_type_slug | product_type_name | collections         | attributes                                                               | rating | tax_class | weight | price | image_url                                                                | brand   | capacity  | weight_attr |
   | ------------------------------- | ------------------------------- | ----------------------------------------------------------------- | ------------- | ------------- | ----------------- | ----------------- | ------------------- | ------------------------------------------------------------------------ | ------ | --------- | ------ | ----- | ------------------------------------------------------------------------ | ------- | --------- | ----------- |
   | Half Dome 2 Tent with Footprint | half-dome-2-tent-with-footprint | Half Dome 2 Tent with Footprint — great for Camping, Backpacking. | tent          | Tent          | tents             | Tents             | camping,backpacking | best-for:camping\|backpacking;persons:2;brand:half                       | 4.7    | standard  | 2.5    | 299.0 | https://www.rei.com/media/09ae9844-d7cf-4450-8a5c-d49b58e3ac23?size=2000 | half    |           |             |
   | Radiant 20 Sleeping Bag         | radiant-20-sleeping-bag         | Radiant 20 Sleeping Bag — great for Camping, Backpacking.         | sleeping-gear | Sleeping Gear | sleeping-bags     | Sleeping Bags     | camping,backpacking | best-for:camping\|backpacking;temp-rating:20;brand:radiant               | 4.7    | standard  | 1.2    | 199.0 | https://www.rei.com/media/e869f452-fda8-41a2-9451-9f876f1c379c?size=2000 | radiant |           |             |
   | Atmos AG 50 Pack - Men's        | atmos-ag-50-pack-men-s          | Atmos AG 50 Pack - Men's — great for Camping, Backpacking.        | backpacks     | Backpacks     | backpacks         | Backpacks         | camping,backpacking | best-for:camping\|backpacking;gender:mens;brand:atmos;capacity:50-person | 4.6    | standard  | 1.5    | 315.0 | https://www.rei.com/media/f0c2dba1-486b-4cae-b140-345b0a5a2519?size=2000 | atmos   | 50-person |             |

   </div>

   ### B) iHerb CSV schema (example: `iherb_product_data - for_saleor_push_v3.csv`)

   - `id`
   - `name`
   - `slug`
   - `main_category` (parent category display name)
   - `main_category_slug` (optional; if absent, generated from `main_category`)
   - `sub_category` (child category display name; optional)
   - `sub_category_slug` (optional; if absent, generated from `sub_category`)
   - `category_name` (leaf category display name; optional)
   - `category_slug` (optional; if absent, generated from `category_name`)
   - `product_type_name`
   - `product_type_slug`
   - `brand`
   - `collections`
   - `tax_class`
   - `breadcrumbs`
   - `short_description`
   - `description_text`
   - `price`
   - `currency`
   - `best_for`
   - `review_score`
   - `review_count`
   - `image_url`
   - `url`

   Category hierarchy logic:

   - If `main_category` present, a root category is created/resolved.
   - If `sub_category` present, it is created under `main_category`.
   - If `category_name` present, it is created under the deepest existing parent (sub if present, else main).
   - If only `category_name` exists (no main/sub), it is created at the root.
   - Slugs are taken from the corresponding `*_slug` columns when provided; otherwise derived from names.

3. **Run the product import script:**
   ```bash
   python load_products_to_saleor.py
   ```

### Output Results CSV

- On each successfully created product, the importer appends a row to the results CSV.
- The output mirrors the input CSV columns and adds two columns at the end:
  - `saleor_product_id`
  - `saleor_variant_id`
- Configure the output path via `OUTPUT_RESULTS_CSV`.

## Notes

- Make sure your Saleor backend is running before importing data
- Configure your `.env` file with the correct Saleor endpoint and API token
- The script will create categories (including parent/child hierarchy for iHerb schema), product types, and collections automatically if they don't exist
- Images will be downloaded and uploaded to your Saleor media storage
- Check the console output for any errors during the import process
- The script uses caching to avoid duplicate API calls - check the `cache/` directory for cached data

### Attribute assignment

- The current run disables product attribute assignment to avoid version-specific API errors in some environments.
- If you need attribute assignment, toggle the `skip_attributes` flag in the product creation call and adjust the mutation shape to your Saleor version.
