from pathlib import Path
import json

from flask import Flask, abort, render_template


BASE_DIR = Path(__file__).resolve().parent
PRODUCTS_FILE = BASE_DIR / "products.json"
IMAGES_DIR = BASE_DIR / "static" / "images"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

CATEGORY_ORDER = [
    "Clutchers",
    "Hair Accessories",
    "Scarves",
    "Bouquets",
    "Keychains",
]


def load_products():
    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        products = json.load(file)

    missing_images = []

    for index, product in enumerate(products, start=1):
        product.setdefault("id", index)
        product.setdefault("slug", product["name"].lower().replace(" ", "-"))
        product.setdefault("images", [product.get("image", "")])
        product.setdefault("category", "Crochet")

        referenced_images = {product.get("image"), *product.get("images", [])}
        for image in referenced_images:
            if image and not (IMAGES_DIR / image).is_file():
                missing_images.append(f"{product['name']}: {image}")

    if missing_images:
        raise FileNotFoundError(
            "Missing product image files: " + ", ".join(missing_images)
        )

    return products


@app.route("/")
def home():
    products = load_products()
    product_categories = {product["category"] for product in products}
    categories = [category for category in CATEGORY_ORDER if category in product_categories]
    return render_template("index.html", products=products, categories=categories)


@app.route("/product/<slug>")
def product_details(slug):
    products = load_products()
    product = next((item for item in products if item["slug"] == slug), None)

    if product is None:
        abort(404)

    return render_template("product_details.html", product=product)


if __name__ == "__main__":
    app.run(debug=True)
