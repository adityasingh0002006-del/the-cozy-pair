from pathlib import Path
import json

from flask import Flask, abort, render_template


BASE_DIR = Path(__file__).resolve().parent
PRODUCTS_FILE = BASE_DIR / "products.json"
IMAGES_DIR = BASE_DIR / "static" / "images"
REVIEWS_DIR = IMAGES_DIR / "reviews"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

GOOGLE_ANALYTICS_ID = "G-PK5H0DPW8E"
GOOGLE_ANALYTICS_SNIPPET = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTICS_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag("js", new Date());
        gtag("config", "{GOOGLE_ANALYTICS_ID}");
    </script>
"""

CATEGORY_ORDER = [
    "Clutchers",
    "Hair Accessories",
    "Scarves",
    "Bouquets",
    "Keychains",
    "Accessories",
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
        product.setdefault("new", False)

        referenced_images = {product.get("image"), *product.get("images", [])}
        for image in referenced_images:
            if image and not (IMAGES_DIR / image).is_file():
                missing_images.append(f"{product['name']}: {image}")

    if missing_images:
        raise FileNotFoundError(
            "Missing product image files: " + ", ".join(missing_images)
        )

    return products


def load_review_images():
    if not REVIEWS_DIR.is_dir():
        return []

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    return [
        f"images/reviews/{image.name}"
        for image in sorted(REVIEWS_DIR.iterdir())
        if image.is_file() and image.suffix.lower() in allowed_extensions
    ]


@app.after_request
def add_google_analytics(response):
    if response.content_type.startswith("text/html"):
        html = response.get_data(as_text=True)
        if GOOGLE_ANALYTICS_ID not in html and "</head>" in html:
            html = html.replace("</head>", f"{GOOGLE_ANALYTICS_SNIPPET}</head>", 1)
            response.set_data(html)

    return response


@app.route("/")
def home():
    products = load_products()
    product_categories = {product["category"] for product in products}
    categories = [category for category in CATEGORY_ORDER if category in product_categories]
    featured_products = products[:4]
    review_images = load_review_images()
    return render_template(
        "index.html",
        products=products,
        categories=categories,
        featured_products=featured_products,
        review_images=review_images,
    )


@app.route("/product/<slug>")
def product_details(slug):
    products = load_products()
    product = next((item for item in products if item["slug"] == slug), None)

    if product is None:
        abort(404)

    return render_template("product_details.html", product=product)


if __name__ == "__main__":
    app.run(debug=True)
