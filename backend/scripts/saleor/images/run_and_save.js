// run_and_save.js
const fs = require("fs");
const path = require("path");
const newman = require("newman");
const archiver = require("archiver");

const COLLECTION_FILE = "./image_downloader.postman_collection.json";
const DATA_FILE = "./images.csv";
const OUT_DIR = "./downloads";
const ZIP_NAME = "images_and_mapping.zip";

if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

const mapping = {}; // original URL -> saved filename
const seenHashes = new Map(); // sha1 -> filename for dedupe
const crypto = require("crypto");

function inferExt(contentType, urlStr) {
	const ct = (contentType || "").toLowerCase();
	if (ct.includes("png")) return ".png";
	if (ct.includes("jpeg") || ct.includes("jpg")) return ".jpg";
	if (ct.includes("webp")) return ".webp";
	if (ct.includes("gif")) return ".gif";
	if (ct.includes("svg")) return ".svg";
	try {
		const u = new URL(urlStr);
		const p = u.pathname.toLowerCase();
		if (p.endsWith(".png")) return ".png";
		if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return ".jpg";
		if (p.endsWith(".webp")) return ".webp";
		if (p.endsWith(".gif")) return ".gif";
		if (p.endsWith(".svg")) return ".svg";
	} catch {}
	return ".jpg";
}

function baseFrom(urlStr) {
	try {
		const u = new URL(urlStr);
		let b = path.basename(u.pathname).split("?")[0] || "image";
		b = b.replace(/\.(png|jpe?g|webp|gif|svg)$/i, "");
		b = b.replace(/[^A-Za-z0-9._-]+/g, "_");
		return b || "image";
	} catch {
		return "image";
	}
}

newman
	.run(
		{
			collection: require(COLLECTION_FILE),
			iterationData: DATA_FILE,
			reporters: "cli",
			timeoutRequest: 180000, // 180s for slow edges
			insecureFileRead: true,
		},
		function (err) {
			if (err) {
				console.error("Newman run failed to start:", err);
				process.exit(1);
			}
		},
	)
	.on("request", (err, args) => {
		if (err) {
			console.error("Request error:", err);
			return;
		}

		const res = args.response;
		if (!res) return;

		const status = res.code;
		const contentType = res.headers.get("Content-Type");
		const isImage = (contentType || "").toLowerCase().startsWith("image/");
		// This is the original URL from your CSV:
		const originalUrl = args.cursor?.iterationData?.url || String(args.request.url);

		if (status >= 200 && status < 300 && isImage) {
			// raw bytes
			const buffer = res.stream; // Buffer
			const sha = crypto.createHash("sha1").update(buffer).digest("hex").slice(0, 16);

			let filename;
			if (seenHashes.has(sha)) {
				filename = seenHashes.get(sha); // dedupe identical bytes
			} else {
				const finalUrl = String(args.request.url);
				const ext = inferExt(contentType, finalUrl);
				let base = baseFrom(finalUrl) + ext;

				// ensure unique on disk
				let stem = base.replace(/\.(png|jpe?g|webp|gif|svg)$/i, "");
				let extn = ext;
				let name = base;
				let k = 1;
				while (fs.existsSync(path.join(OUT_DIR, name))) {
					name = `${stem}_${k}${extn}`;
					k++;
				}
				fs.writeFileSync(path.join(OUT_DIR, name), buffer);
				filename = name;
				seenHashes.set(sha, filename);
			}
			mapping[originalUrl] = filename;
			console.log(`Saved: ${mapping[originalUrl]}  <--  ${originalUrl}`);
		} else {
			console.warn(`Skipped (status/content-type): ${status} ${contentType}  ${String(args.request.url)}`);
		}
	})
	.on("done", (err, summary) => {
		if (err) {
			console.error("Run errored:", err);
			process.exit(1);
		}

		// write mapping.json
		const mapPath = path.join(OUT_DIR, "mapping.json");
		fs.writeFileSync(mapPath, JSON.stringify(mapping, null, 2), "utf8");

		// zip everything
		const zipPath = path.join(".", ZIP_NAME);
		const output = fs.createWriteStream(zipPath);
		const archive = archiver("zip", { zlib: { level: 9 } });

		output.on("close", () => {
			console.log(`\nZip written: ${zipPath}  (${archive.pointer()} bytes)`);
			console.log(`Images dir: ${OUT_DIR}`);
			console.log(`Mapping:    ${mapPath}`);
		});
		archive.on("error", (err) => {
			throw err;
		});

		archive.pipe(output);
		archive.directory(OUT_DIR, false);
		archive.finalize();
	});
