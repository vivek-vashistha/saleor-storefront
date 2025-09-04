newman run "image_downloader.postman_collection.json" \
  -d ./images/images.csv \
  --reporters cli,json \
  --reporter-json-export out.json