
import json
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    send_from_directory,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from werkzeug.utils import secure_filename


# ===========================================================================
# AI MODULES
# ===========================================================================

from ai.catalog_ai import generate_catalog
from ai.price_prediction import suggest_price
from ai.demand_prediction import predict_demand
from ai.market_matching import match_markets
from ai.image_enhancement import enhance_image


# ===========================================================================
# APPLICATION CONFIGURATION
# ===========================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "products"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
}

SUPPORTED_LANGUAGES = [
    "en",
    "mr",
    "hi",
]

DEFAULT_LANGUAGE = "en"


app = Flask(__name__)

app.secret_key = "kalasetu-prototype-secret-key"

app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024


os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ===========================================================================
# JSON HELPERS
# ===========================================================================

def _data_path(filename):
    return os.path.join(
        DATA_DIR,
        filename
    )


def read_json(filename):
    """
    Safely read JSON file.
    Returns [] if file does not exist, is empty, or invalid.
    """

    path = _data_path(filename)

    if not os.path.exists(path):
        return []

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read().strip()

            if not content:
                return []

            return json.loads(content)

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return []


def write_json(filename, data):

    path = _data_path(filename)

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


# ===========================================================================
# TRANSLATION
# ===========================================================================

def load_translations():
    return read_json(
        "translations.json"
    )


def t(key, lang=None, **kwargs):

    lang = (
        lang
        or session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )

    translations = load_translations()

    if not isinstance(
        translations,
        dict
    ):
        return key

    default_dict = translations.get(
        DEFAULT_LANGUAGE,
        {}
    )

    lang_dict = translations.get(
        lang,
        default_dict
    )

    if not isinstance(
        lang_dict,
        dict
    ):
        lang_dict = default_dict

    text = (
        lang_dict.get(key)
        or default_dict.get(key)
        or key
    )

    if kwargs:

        try:
            text = text.format(**kwargs)

        except (
            KeyError,
            IndexError,
            ValueError,
        ):
            pass

    return text


# ===========================================================================
# JINJA GLOBALS
# ===========================================================================

@app.context_processor
def inject_globals():

    lang = session.get(
        "language",
        DEFAULT_LANGUAGE
    )

    return {
        "t": t,
        "current_lang": lang,
        "supported_languages": SUPPORTED_LANGUAGES,
        "artisan_name": session.get(
            "artisan_name"
        ),
    }


# ===========================================================================
# FILE VALIDATION
# ===========================================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# ===========================================================================
# ARTISAN HELPERS
# ===========================================================================

def get_current_artisan():

    artisan_id = session.get(
        "artisan_id"
    )

    if artisan_id is None:
        return None

    artisans = read_json(
        "artisans.json"
    )

    if not isinstance(
        artisans,
        list
    ):
        return None

    for artisan in artisans:

        if (
            artisan.get("artisan_id")
            == artisan_id
        ):
            return artisan

    return None


def login_required(view_func):

    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if not session.get(
            "artisan_id"
        ):
            return redirect(
                url_for("artisan_login")
            )

        return view_func(
            *args,
            **kwargs
        )

    return wrapped


# ===========================================================================
# LANDING / LANGUAGE
# ===========================================================================

@app.route("/")
def index():

    return redirect(
        url_for("choose_language")
    )


@app.route(
    "/language",
    methods=["GET", "POST"]
)
def choose_language():

    if request.method == "POST":

        language = request.form.get(
            "language",
            DEFAULT_LANGUAGE
        )

        if language not in SUPPORTED_LANGUAGES:
            language = DEFAULT_LANGUAGE

        session["language"] = language
        session.permanent = True

        return redirect(
            url_for("role_selection")
        )

    return render_template(
        "language.html"
    )


@app.route(
    "/set-language",
    methods=["POST"]
)
def set_language():

    if request.is_json:

        data = request.get_json(
            silent=True
        ) or {}

        language = data.get(
            "language"
        )

    else:

        language = request.form.get(
            "language"
        )

    if language not in SUPPORTED_LANGUAGES:

        return jsonify({
            "success": False,
            "error": "Unsupported language",
        }), 400

    session["language"] = language
    session.permanent = True

    artisan = get_current_artisan()

    if artisan:

        artisans = read_json(
            "artisans.json"
        )

        if isinstance(
            artisans,
            list
        ):

            for item in artisans:

                if (
                    item.get("artisan_id")
                    == artisan.get("artisan_id")
                ):

                    item["language"] = language
                    break

            write_json(
                "artisans.json",
                artisans
            )

    return jsonify({
        "success": True,
        "language": language,
    })


# ===========================================================================
# ROLE SELECTION
# ===========================================================================

@app.route("/role-selection")
def role_selection():

    if not session.get(
        "language"
    ):
        return redirect(
            url_for("choose_language")
        )

    return render_template(
        "role_selection.html"
    )


# ===========================================================================
# ARTISAN REGISTER
# ===========================================================================

@app.route(
    "/artisan/register",
    methods=["GET", "POST"]
)
def artisan_register():

    if not session.get("language"):
        return redirect(
            url_for("choose_language")
        )

    error = None

    current_language = session.get(
        "language",
        DEFAULT_LANGUAGE
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if (
            not name
            or not mobile
            or not location
            or not password
        ):

            error = t(
                "register_required"
            )

            return render_template(
                "artisan/register.html",
                error=error
            )

        if (
            not mobile.isdigit()
            or len(mobile) != 10
        ):

            error = t(
                "invalid_mobile"
            )

            return render_template(
                "artisan/register.html",
                error=error
            )

        artisans = read_json(
            "artisans.json"
        )

        if not isinstance(
            artisans,
            list
        ):
            artisans = []

        for artisan in artisans:

            if (
                str(
                    artisan.get(
                        "mobile",
                        ""
                    )
                ).strip()
                == mobile
            ):

                error = t(
                    "mobile_already_registered"
                )

                return render_template(
                    "artisan/register.html",
                    error=error
                )

        artisan_ids = []

        for artisan in artisans:

            try:

                artisan_ids.append(
                    int(
                        artisan.get(
                            "artisan_id"
                        )
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

        new_artisan_id = (
            max(artisan_ids) + 1
            if artisan_ids
            else 1
        )

        new_artisan = {
            "artisan_id": new_artisan_id,
            "name": name,
            "mobile": mobile,
            "password": password,
            "location": location,
            "language": current_language,
            "profile_image": "/static/images/default_artisan.png",
        }

        artisans.append(
            new_artisan
        )

        write_json(
            "artisans.json",
            artisans
        )

        session["artisan_id"] = new_artisan_id
        session["artisan_name"] = name
        session["language"] = current_language

        return redirect(
            url_for(
                "artisan_dashboard"
            )
        )

    return render_template(
        "artisan/register.html",
        error=error
    )


# ===========================================================================
# ARTISAN LOGIN
# ===========================================================================

@app.route(
    "/artisan/login",
    methods=["GET", "POST"]
)
def artisan_login():

    if not session.get(
        "language"
    ):
        return redirect(
            url_for("choose_language")
        )

    error = None

    if request.method == "POST":

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        artisans = read_json(
            "artisans.json"
        )

        if not isinstance(
            artisans,
            list
        ):
            artisans = []

        matched_artisan = next(
            (
                artisan
                for artisan in artisans
                if (
                    str(
                        artisan.get(
                            "mobile",
                            ""
                        )
                    ).strip()
                    == mobile
                    and str(
                        artisan.get(
                            "password",
                            ""
                        )
                    ).strip()
                    == password
                )
            ),
            None
        )

        if matched_artisan:

            session["artisan_id"] = (
                matched_artisan.get(
                    "artisan_id"
                )
            )

            session["artisan_name"] = (
                matched_artisan.get(
                    "name",
                    "Artisan"
                )
            )

            if not session.get(
                "language"
            ):

                session["language"] = (
                    matched_artisan.get(
                        "language",
                        DEFAULT_LANGUAGE
                    )
                )

            return redirect(
                url_for(
                    "artisan_dashboard"
                )
            )

        error = t(
            "login_error"
        )

    return render_template(
        "artisan/login.html",
        error=error
    )


@app.route("/artisan/logout")
def artisan_logout():

    session.pop(
        "artisan_id",
        None
    )

    session.pop(
        "artisan_name",
        None
    )

    session.pop(
        "pending_product",
        None
    )

    return redirect(
        url_for("artisan_login")
    )


# ===========================================================================
# ARTISAN DASHBOARD
# ===========================================================================

# ===========================================================================
# ARTISAN DASHBOARD
# ===========================================================================

@app.route("/artisan/dashboard")
@login_required
def artisan_dashboard():

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    # -----------------------------------------------------------------------
    # PRODUCTS
    # -----------------------------------------------------------------------

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    my_products = [
        product
        for product in products
        if (
            str(product.get("artisan_id"))
            == str(artisan.get("artisan_id"))
        )
    ]

    recent_products = sorted(
        my_products,
        key=lambda product: product.get(
            "created_at",
            ""
        ),
        reverse=True
    )[:3]


    # -----------------------------------------------------------------------
    # CUSTOMER ORDERS
    # -----------------------------------------------------------------------

    orders = read_json(
        "orders.json"
    )

    if not isinstance(
        orders,
        list
    ):
        orders = []

    artisan_orders = [
        order
        for order in orders
        if (
            str(order.get("artisan_id"))
            == str(artisan.get("artisan_id"))
        )
    ]

    # Latest orders first
    artisan_orders = sorted(
        artisan_orders,
        key=lambda order: order.get(
            "created_at",
            ""
        ),
        reverse=True
    )


    # -----------------------------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------------------------

    return render_template(
        "artisan/dashboard.html",
        artisan=artisan,
        recent_products=recent_products,
        artisan_orders=artisan_orders
    )
# ===========================================================================
# ARTISAN CUSTOMER ORDERS
# ===========================================================================

@app.route("/artisan/orders")
@login_required
def artisan_orders():

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    orders = read_json(
        "orders.json"
    )

    if not isinstance(
        orders,
        list
    ):
        orders = []

    artisan_orders = [
        order
        for order in orders
        if (
            str(order.get("artisan_id"))
            == str(artisan.get("artisan_id"))
        )
    ]

    artisan_orders = sorted(
        artisan_orders,
        key=lambda order: order.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    return render_template(
        "artisan/orders.html",
        artisan=artisan,
        orders=artisan_orders
    )

# ===========================================================================
# ADD PRODUCT
# ===========================================================================

@app.route("/artisan/add-product")
@login_required
def add_product():

    session["pending_product"] = {}

    return render_template(
        "artisan/add_product.html"
    )


# ===========================================================================
# UPLOAD THREE PRODUCT PHOTOS
# ===========================================================================

@app.route(
    "/artisan/upload-image",
    methods=["POST"]
)
@login_required
def upload_image():

    photo_fields = {
        "front": "front_image",
        "side": "side_image",
        "detail": "detail_image",
    }

    files_to_process = {}

    for view_name, field_name in photo_fields.items():

        uploaded_file = request.files.get(
            field_name
        )

        if (
            uploaded_file is None
            or uploaded_file.filename == ""
        ):

            return jsonify({
                "success": False,
                "error": (
                    f"Please upload the "
                    f"{view_name} photo."
                ),
            }), 400

        if not allowed_file(
            uploaded_file.filename
        ):

            return jsonify({
                "success": False,
                "error": (
                    f"Invalid {view_name} photo. "
                    "Use JPG, JPEG, PNG or WEBP."
                ),
            }), 400

        files_to_process[
            view_name
        ] = uploaded_file

    pending = session.get(
        "pending_product",
        {}
    )

    if not isinstance(
        pending,
        dict
    ):
        pending = {}

    uploaded_images = {}

    for view_name, uploaded_file in files_to_process.items():

        safe_filename = secure_filename(
            uploaded_file.filename
        )

        extension = os.path.splitext(
            safe_filename
        )[1].lower().replace(
            ".",
            ""
        )

        if extension not in ALLOWED_EXTENSIONS:

            return jsonify({
                "success": False,
                "error": (
                    f"Invalid {view_name} image."
                ),
            }), 400

        unique_id = uuid.uuid4().hex

        original_name = (
            f"{view_name}_original_"
            f"{unique_id}.{extension}"
        )

        enhanced_name = (
            f"{view_name}_enhanced_"
            f"{unique_id}.{extension}"
        )

        original_path = os.path.join(
            UPLOAD_DIR,
            original_name
        )

        enhanced_path = os.path.join(
            UPLOAD_DIR,
            enhanced_name
        )

        try:

            uploaded_file.save(
                original_path
            )

        except Exception:

            app.logger.exception(
                "Could not save %s image",
                view_name
            )

            return jsonify({
                "success": False,
                "error": (
                    f"Could not save the "
                    f"{view_name} photo."
                ),
            }), 500

        enhancement_ok = True

        try:

            enhance_image(
                original_path,
                enhanced_path
            )

        except Exception:

            app.logger.exception(
                "Image enhancement failed for %s",
                view_name
            )

            enhanced_name = original_name
            enhanced_path = original_path
            enhancement_ok = False

        original_url = url_for(
            "uploaded_product_file",
            filename=original_name
        )

        enhanced_url = url_for(
            "uploaded_product_file",
            filename=enhanced_name
        )

        uploaded_images[
            view_name
        ] = {
            "original": original_url,
            "enhanced": enhanced_url,
            "enhancement_ok": enhancement_ok,
        }

    pending["images"] = uploaded_images

    pending["original_images"] = {
        "front": uploaded_images[
            "front"
        ]["original"],

        "side": uploaded_images[
            "side"
        ]["original"],

        "detail": uploaded_images[
            "detail"
        ]["original"],
    }

    pending["enhanced_images"] = {
        "front": uploaded_images[
            "front"
        ]["enhanced"],

        "side": uploaded_images[
            "side"
        ]["enhanced"],

        "detail": uploaded_images[
            "detail"
        ]["enhanced"],
    }

    pending["original_image"] = (
        uploaded_images[
            "front"
        ]["original"]
    )

    pending["enhanced_image"] = (
        uploaded_images[
            "front"
        ]["enhanced"]
    )

    pending["final_image"] = (
        uploaded_images[
            "front"
        ]["enhanced"]
    )

    session["pending_product"] = pending
    session.modified = True

    return jsonify({

        "success": True,

        "front": uploaded_images[
            "front"
        ]["enhanced"],

        "front_original": uploaded_images[
            "front"
        ]["original"],

        "front_enhanced": uploaded_images[
            "front"
        ]["enhanced"],

        "side": uploaded_images[
            "side"
        ]["enhanced"],

        "side_original": uploaded_images[
            "side"
        ]["original"],

        "side_enhanced": uploaded_images[
            "side"
        ]["enhanced"],

        "detail": uploaded_images[
            "detail"
        ]["enhanced"],

        "detail_original": uploaded_images[
            "detail"
        ]["original"],

        "detail_enhanced": uploaded_images[
            "detail"
        ]["enhanced"],

        "images": uploaded_images,

        "enhancement_ok": all(
            image.get(
                "enhancement_ok",
                False
            )
            for image in uploaded_images.values()
        ),
    })


# ===========================================================================
# CHOOSE ORIGINAL OR ENHANCED IMAGE
# ===========================================================================

@app.route(
    "/artisan/choose-image",
    methods=["POST"]
)
@login_required
def choose_image():

    choice = request.form.get(
        "choice",
        "enhanced"
    )

    pending = session.get(
        "pending_product",
        {}
    )

    if not isinstance(
        pending,
        dict
    ):
        pending = {}

    images = pending.get(
        "images",
        {}
    )

    if not images:
        return redirect(
            url_for("add_product")
        )

    required_views = [
        "front",
        "side",
        "detail",
    ]

    for view_name in required_views:

        if view_name not in images:

            return redirect(
                url_for("add_product")
            )

    if choice == "enhanced":

        final_images = {
            "front": images[
                "front"
            ]["enhanced"],

            "side": images[
                "side"
            ]["enhanced"],

            "detail": images[
                "detail"
            ]["enhanced"],
        }

    else:

        choice = "original"

        final_images = {
            "front": images[
                "front"
            ]["original"],

            "side": images[
                "side"
            ]["original"],

            "detail": images[
                "detail"
            ]["original"],
        }

    pending["final_images"] = final_images

    pending["final_image"] = (
        final_images["front"]
    )

    pending["image_choice"] = choice

    session["pending_product"] = pending
    session.modified = True

    return redirect(
        url_for("artisan_questions")
    )


# ===========================================================================
# ARTISAN QUESTIONS
# ===========================================================================

@app.route("/artisan/questions")
@login_required
def artisan_questions():

    pending = session.get(
        "pending_product",
        {}
    )

    if not pending.get(
        "final_image"
    ):

        return redirect(
            url_for("add_product")
        )

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    questions = [
        {
            "key": "material",
            "text": t("q_material"),
        },
        {
            "key": "making_time",
            "text": t("q_making_time"),
        },
        {
            "key": "making_cost",
            "text": t("q_making_cost"),
        },
        {
            "key": "size",
            "text": t("q_size"),
        },
    ]

    speech_lang_map = {
        "en": "en-IN",
        "mr": "mr-IN",
        "hi": "hi-IN",
    }

    speech_lang = speech_lang_map.get(
        session.get(
            "language",
            DEFAULT_LANGUAGE
        ),
        "en-IN"
    )

    return render_template(
        "artisan/questions.html",
        questions=questions,
        artisan=artisan,
        speech_lang=speech_lang
    )


# ===========================================================================
# GENERATE AI CATALOG
# ===========================================================================

@app.route(
    "/artisan/generate-catalog",
    methods=["POST"]
)
@login_required
def generate_catalog_route():

    artisan = get_current_artisan()

    if not artisan:

        return jsonify({
            "success": False,
            "message": "Artisan session not found.",
        }), 401

    pending = session.get(
        "pending_product",
        {}
    )

    final_image = pending.get(
        "final_image"
    )

    if not final_image:

        return jsonify({
            "success": False,
            "message": (
                "Please select a product image first."
            ),
        }), 400

    answers = {
        "material": request.form.get(
            "answer_0",
            ""
        ).strip(),

        "making_time": request.form.get(
            "answer_1",
            ""
        ).strip(),

        "making_cost": request.form.get(
            "answer_2",
            ""
        ).strip(),

        "size": request.form.get(
            "answer_3",
            ""
        ).strip(),
    }

    for field, message in [
        (
            "material",
            "Please provide the material."
        ),
        (
            "making_time",
            "Please provide the making time."
        ),
        (
            "making_cost",
            "Please provide the making cost."
        ),
        (
            "size",
            "Please provide the product size."
        ),
    ]:

        if not answers[field]:

            return jsonify({
                "success": False,
                "message": message,
            }), 400

    product_data = {
        "material": answers[
            "material"
        ],

        "making_time": answers[
            "making_time"
        ],

        "making_cost": answers[
            "making_cost"
        ],

        "size": answers[
            "size"
        ],
    }

    language = session.get(
        "language",
        DEFAULT_LANGUAGE
    )

    try:

        catalog_draft = generate_catalog(
            product_data,
            language
        )

    except Exception:

        app.logger.exception(
            "Catalog generation error"
        )

        return jsonify({
            "success": False,
            "message": (
                "Unable to generate catalog."
            ),
        }), 500

    try:

        price = suggest_price(
            product_data
        )

    except Exception:

        app.logger.exception(
            "Price suggestion error"
        )

        price = {
            "min_price": 0,
            "max_price": 0,
            "recommended_price": 0,
        }

    pending["answers"] = answers
    pending["draft"] = catalog_draft

    pending["suggested_price_min"] = (
        price.get(
            "min_price",
            0
        )
    )

    pending["suggested_price_max"] = (
        price.get(
            "max_price",
            0
        )
    )

    pending["recommended_price"] = (
        price.get(
            "recommended_price",
            0
        )
    )

    pending["final_price"] = (
        price.get(
            "recommended_price",
            0
        )
        or price.get(
            "min_price",
            0
        )
        or 0
    )

    session["pending_product"] = pending
    session.modified = True

    return jsonify({
        "success": True,
        "redirect": url_for(
            "catalog_review"
        ),
    })


# ===========================================================================
# CATALOG REVIEW
# ===========================================================================

@app.route(
    "/artisan/catalog-review",
    methods=["GET", "POST"]
)
@login_required
def catalog_review():

    pending = session.get(
        "pending_product",
        {}
    )

    if not isinstance(
        pending,
        dict
    ):
        pending = {}

    if not pending.get(
        "draft"
    ):

        return redirect(
            url_for("add_product")
        )

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    draft = pending.get(
        "draft",
        {}
    )

    if not isinstance(
        draft,
        dict
    ):
        draft = {}

    if request.method == "POST":

        action = request.form.get(
            "action",
            "save"
        )

        draft["name"] = request.form.get(
            "name",
            draft.get(
                "name",
                ""
            )
        ).strip()

        draft["description"] = request.form.get(
            "description",
            draft.get(
                "description",
                ""
            )
        ).strip()

        draft["material"] = request.form.get(
            "material",
            draft.get(
                "material",
                ""
            )
        ).strip()

        draft["size"] = request.form.get(
            "size",
            draft.get(
                "size",
                ""
            )
        ).strip()

        target_market_text = request.form.get(
            "target_market",
            ""
        ).strip()

        if target_market_text:

            draft["target_market"] = [
                market.strip()
                for market in target_market_text.split(",")
                if market.strip()
            ]

        elif not draft.get(
            "target_market"
        ):

            draft["target_market"] = []

        if "making_time" not in draft:

            draft["making_time"] = (
                pending.get(
                    "answers",
                    {}
                ).get(
                    "making_time",
                    ""
                )
            )

        if "making_cost" not in draft:

            draft["making_cost"] = (
                pending.get(
                    "answers",
                    {}
                ).get(
                    "making_cost",
                    0
                )
            )

        final_price_raw = request.form.get(
            "final_price",
            ""
        ).strip()

        try:

            final_price_value = float(
                final_price_raw
            )

        except (
            TypeError,
            ValueError,
        ):

            final_price_value = float(
                pending.get(
                    "recommended_price",
                    pending.get(
                        "suggested_price_min",
                        0
                    )
                ) or 0
            )

        pending["draft"] = draft
        pending["final_price"] = (
            final_price_value
        )

        session["pending_product"] = pending
        session.modified = True

        if action != "approve":

            return redirect(
                url_for("catalog_review")
            )

        # ---------------------------------------------------------------
        # APPROVE AND PUBLISH
        # ---------------------------------------------------------------

        products = read_json(
            "products.json"
        )

        if not isinstance(
            products,
            list
        ):
            products = []

        product_ids = []

        for product in products:

            try:

                product_ids.append(
                    int(
                        product.get(
                            "product_id",
                            0
                        )
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

        new_product_id = (
            max(
                product_ids,
                default=0
            ) + 1
        )

        try:

            making_cost_value = float(
                draft.get(
                    "making_cost",
                    pending.get(
                        "answers",
                        {}
                    ).get(
                        "making_cost",
                        0
                    )
                ) or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            making_cost_value = 0

        try:

            final_price_value = float(
                pending.get(
                    "final_price",
                    0
                ) or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            final_price_value = 0

        final_images = pending.get(
            "final_images",
            {}
        )

        if not isinstance(
            final_images,
            dict
        ):
            final_images = {}

        final_image = pending.get(
            "final_image"
        )

        if (
            not final_images
            and final_image
        ):

            final_images = {
                "front": final_image,
                "side": final_image,
                "detail": final_image,
            }

        target_market = draft.get(
            "target_market",
            []
        )

        if isinstance(
            target_market,
            str
        ):

            target_market = [
                market.strip()
                for market in target_market.split(",")
                if market.strip()
            ]

        if not isinstance(
            target_market,
            list
        ):

            target_market = []

        now = datetime.now().isoformat()

        new_product = {

            "product_id": new_product_id,

            "artisan_id": artisan.get(
                "artisan_id"
            ),

            "artisan_name": artisan.get(
                "name",
                ""
            ),

            "image": final_images.get(
                "front",
                final_image
            ),

            "final_image": final_images.get(
                "front",
                final_image
            ),

            "images": final_images,

            "front_image": final_images.get(
                "front"
            ),

            "side_image": final_images.get(
                "side"
            ),

            "detail_image": final_images.get(
                "detail"
            ),

            "original_images": pending.get(
                "original_images",
                {}
            ),

            "original_image": pending.get(
                "original_image"
            ),

            "enhanced_images": pending.get(
                "enhanced_images",
                {}
            ),

            "name": draft.get(
                "name",
                ""
            ),

            "description": draft.get(
                "description",
                ""
            ),

            "material": draft.get(
                "material",
                ""
            ),

            "size": draft.get(
                "size",
                ""
            ),

            "target_market": target_market,

            "making_time": draft.get(
                "making_time",
                ""
            ),

            "making_cost": making_cost_value,

            "suggested_price_min": pending.get(
                "suggested_price_min",
                0
            ),

            "suggested_price_max": pending.get(
                "suggested_price_max",
                0
            ),

            "recommended_price": pending.get(
                "recommended_price",
                0
            ),

            "final_price": final_price_value,

            "status": "published",

            "approval_status": "approved",

            "image_choice": pending.get(
                "image_choice",
                "enhanced"
            ),

            "created_at": now,

            "published_at": now,
        }

        products.append(
            new_product
        )

        try:

            write_json(
                "products.json",
                products
            )

        except Exception:

            app.logger.exception(
                "Could not save product"
            )

            return render_template(
                "artisan/catalog_review.html",
                pending=pending,
                artisan=artisan,
                error=(
                    "Could not save product. "
                    "Please try again."
                )
            )

        session.pop(
            "pending_product",
            None
        )

        session.modified = True

        return redirect(
            url_for(
                "my_products",
                published="1"
            )
        )

    return render_template(
        "artisan/catalog_review.html",
        pending=pending,
        artisan=artisan
    )


# ===========================================================================
# MY PRODUCTS
# ===========================================================================

@app.route("/artisan/products")
@login_required
def my_products():

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    mine = [
        product
        for product in products
        if (
            product.get("artisan_id")
            == artisan.get("artisan_id")
        )
    ]

    mine.sort(
        key=lambda product: product.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    just_published = (
        request.args.get(
            "published"
        ) == "1"
    )

    return render_template(
        "artisan/my_products.html",
        products=mine,
        just_published=just_published
    )


# ===========================================================================
# DEMAND INSIGHTS
# ===========================================================================

@app.route("/artisan/demand")
@login_required
def demand_insights():

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    mine = [
        product
        for product in products
        if (
            product.get("artisan_id")
            == artisan.get("artisan_id")
        )
    ]

    selected_id = request.args.get(
        "product_id",
        type=int
    )

    selected_product = None

    if mine:

        if selected_id:

            selected_product = next(
                (
                    product
                    for product in mine
                    if (
                        product.get(
                            "product_id"
                        )
                        == selected_id
                    )
                ),
                mine[0]
            )

        else:

            selected_product = mine[0]

    demand = None
    markets = []

    if selected_product:

        try:

            demand = predict_demand(
                selected_product.get(
                    "product_id"
                )
            )

        except Exception:

            app.logger.exception(
                "Demand prediction failed"
            )

        all_markets = read_json(
            "markets.json"
        )

        if not isinstance(
            all_markets,
            list
        ):
            all_markets = []

        try:

            markets = match_markets(
                selected_product,
                all_markets
            )

        except Exception:

            app.logger.exception(
                "Market matching failed"
            )

            markets = []

    return render_template(
        "artisan/demand.html",
        products=mine,
        selected_product=selected_product,
        demand=demand,
        markets=markets
    )


# ===========================================================================
# ARTISAN PROFILE
# ===========================================================================

@app.route(
    "/artisan/profile",
    methods=["GET", "POST"]
)
@login_required
def artisan_profile():

    artisan = get_current_artisan()

    if not artisan:

        session.clear()

        return redirect(
            url_for("artisan_login")
        )

    if request.method == "POST":

        language = request.form.get(
            "language",
            DEFAULT_LANGUAGE
        )

        if language in SUPPORTED_LANGUAGES:

            session["language"] = language

            artisans = read_json(
                "artisans.json"
            )

            if isinstance(
                artisans,
                list
            ):

                for item in artisans:

                    if (
                        item.get(
                            "artisan_id"
                        )
                        == artisan.get(
                            "artisan_id"
                        )
                    ):

                        item["language"] = language
                        break

                write_json(
                    "artisans.json",
                    artisans
                )

        return redirect(
            url_for("artisan_profile")
        )

    return render_template(
        "artisan/profile.html",
        artisan=artisan
    )


# ===========================================================================
# SERVE PRODUCT UPLOADS
# ===========================================================================

@app.route(
    "/uploads/products/<path:filename>"
)
def uploaded_product_file(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# ===========================================================================
# CUSTOMER HOME / MARKETPLACE
# ===========================================================================

@app.route("/customer")
def customer_home():

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    customer_products = []

    for product in products:

        if (
            product.get("status")
            != "published"
            or product.get(
                "approval_status"
            )
            != "approved"
        ):
            continue

        enhanced_images = product.get(
            "enhanced_images",
            {}
        )

        if not isinstance(
            enhanced_images,
            dict
        ):
            enhanced_images = {}

        customer_product = {

            "product_id": product.get(
                "product_id"
            ),

            "name": product.get(
                "name",
                ""
            ),

            "description": product.get(
                "description",
                ""
            ),

            "material": product.get(
                "material",
                ""
            ),

            "size": product.get(
                "size",
                ""
            ),

            "artisan_name": product.get(
                "artisan_name",
                ""
            ),

            "final_price": product.get(
                "final_price"
            ),

            "image": (
                product.get(
                    "final_image"
                )
                or product.get(
                    "image"
                )
                or product.get(
                    "front_image"
                )
            ),

            "images": {

                "front": (
                    enhanced_images.get(
                        "front"
                    )
                    or product.get(
                        "front_image"
                    )
                    or product.get(
                        "final_image"
                    )
                    or product.get(
                        "image"
                    )
                ),

                "side": (
                    enhanced_images.get(
                        "side"
                    )
                    or product.get(
                        "side_image"
                    )
                ),

                "detail": (
                    enhanced_images.get(
                        "detail"
                    )
                    or product.get(
                        "detail_image"
                    )
                ),
            },
        }

        customer_products.append(
            customer_product
        )

    return render_template(
        "customer/home.html",
        products=customer_products,
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# CUSTOMER PRODUCT DETAILS
# ===========================================================================

@app.route(
    "/customer/product/<int:product_id>"
)
def product_details(product_id):

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    product = next(
        (
            p
            for p in products
            if (
                p.get(
                    "product_id"
                )
                == product_id
                and p.get(
                    "status"
                )
                == "published"
                and p.get(
                    "approval_status"
                )
                == "approved"
            )
        ),
        None
    )

    if product is None:

        return (
            "Product not found",
            404
        )

    enhanced_images = product.get(
        "enhanced_images",
        {}
    )

    if not isinstance(
        enhanced_images,
        dict
    ):
        enhanced_images = {}

    customer_product = {

        "product_id": product.get(
            "product_id"
        ),

        "name": product.get(
            "name",
            ""
        ),

        "description": product.get(
            "description",
            ""
        ),

        "material": product.get(
            "material",
            ""
        ),

        "size": product.get(
            "size",
            ""
        ),

        "artisan_name": product.get(
            "artisan_name",
            ""
        ),

        "final_price": product.get(
            "final_price"
        ),

        "images": {

            "front": (
                enhanced_images.get(
                    "front"
                )
                or product.get(
                    "front_image"
                )
                or product.get(
                    "final_image"
                )
                or product.get(
                    "image"
                )
            ),

            "side": (
                enhanced_images.get(
                    "side"
                )
                or product.get(
                    "side_image"
                )
            ),

            "detail": (
                enhanced_images.get(
                    "detail"
                )
                or product.get(
                    "detail_image"
                )
            ),
        },
    }

    return render_template(
        "customer/product_details.html",
        product=customer_product,
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# CUSTOMER BUY NOW
# ===========================================================================

@app.route(
    "/customer/buy/<int:product_id>"
)
def customer_buy(product_id):

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    product = next(
        (
            p
            for p in products
            if (
                p.get(
                    "product_id"
                )
                == product_id
                and p.get(
                    "status"
                )
                == "published"
                and p.get(
                    "approval_status"
                )
                == "approved"
            )
        ),
        None
    )

    if product is None:

        return (
            "Product not found",
            404
        )

    if not session.get(
        "customer_logged_in"
    ):

        session[
            "pending_checkout_product_id"
        ] = product_id

        return redirect(
            url_for(
                "customer_login"
            )
        )

    return redirect(
        url_for(
            "customer_checkout",
            product_id=product_id
        )
    )


# ===========================================================================
# CUSTOMER PROFILE
# ===========================================================================

@app.route("/customer/profile")
def customer_profile():

    if not session.get(
        "customer_logged_in"
    ):

        return redirect(
            url_for("customer_login")
        )

    customers = read_json(
        "customers.json"
    )

    if not isinstance(
        customers,
        list
    ):
        customers = []

    customer_id = session.get(
        "customer_id"
    )

    customer = next(
        (
            c
            for c in customers
            if (
                c.get(
                    "customer_id"
                )
                == customer_id
            )
        ),
        None
    )

    if not customer:

        session.clear()

        return redirect(
            url_for("customer_login")
        )

    return render_template(
        "customer/profile.html",
        customer=customer,
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# CUSTOMER LOGOUT
# ===========================================================================

@app.route("/customer/logout")
def customer_logout():

    session.pop(
        "customer_logged_in",
        None
    )

    session.pop(
        "customer_id",
        None
    )

    session.pop(
        "customer_mobile",
        None
    )

    session.pop(
        "customer_name",
        None
    )

    session.pop(
        "customer_address",
        None
    )

    session.pop(
        "pending_checkout_product_id",
        None
    )

    return redirect(
        url_for("customer_home")
    )


# ===========================================================================
# CUSTOMER CHECKOUT
# ===========================================================================

@app.route(
    "/customer/checkout/<int:product_id>"
)
def customer_checkout(product_id):

    if not session.get(
        "customer_logged_in"
    ):

        session[
            "pending_checkout_product_id"
        ] = product_id

        return redirect(
            url_for(
                "customer_login"
            )
        )

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    product = next(
        (
            p
            for p in products
            if (
                p.get(
                    "product_id"
                )
                == product_id
                and p.get(
                    "status"
                )
                == "published"
                and p.get(
                    "approval_status"
                )
                == "approved"
            )
        ),
        None
    )

    if product is None:

        return (
            "Product not found",
            404
        )

    enhanced_images = product.get(
        "enhanced_images",
        {}
    )

    if not isinstance(
        enhanced_images,
        dict
    ):
        enhanced_images = {}

    customer_product = {

        "product_id": product.get(
            "product_id"
        ),

        "name": product.get(
            "name",
            ""
        ),

        "description": product.get(
            "description",
            ""
        ),

        "material": product.get(
            "material",
            ""
        ),

        "size": product.get(
            "size",
            ""
        ),

        "artisan_name": product.get(
            "artisan_name",
            ""
        ),

        "final_price": product.get(
            "final_price"
        ),

        "images": {

            "front": (
                enhanced_images.get(
                    "front"
                )
                or product.get(
                    "front_image"
                )
                or product.get(
                    "final_image"
                )
                or product.get(
                    "image"
                )
            ),

            "side": (
                enhanced_images.get(
                    "side"
                )
                or product.get(
                    "side_image"
                )
            ),

            "detail": (
                enhanced_images.get(
                    "detail"
                )
                or product.get(
                    "detail_image"
                )
            ),
        },
    }

    customers = read_json(
        "customers.json"
    )

    if not isinstance(
        customers,
        list
    ):
        customers = []

    customer_id = session.get(
        "customer_id"
    )

    customer = next(
        (
            c
            for c in customers
            if (
                c.get(
                    "customer_id"
                )
                == customer_id
            )
        ),
        None
    )

    if customer is None:

        session.clear()

        return redirect(
            url_for("customer_login")
        )

    return render_template(
        "customer/checkout.html",
        product=customer_product,
        customer=customer,
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# CUSTOMER PLACE ORDER
# ===========================================================================

@app.route(
    "/customer/place-order/<int:product_id>",
    methods=["POST"]
)
def place_order(product_id):

    if not session.get(
        "customer_logged_in"
    ):

        session[
            "pending_checkout_product_id"
        ] = product_id

        return redirect(
            url_for(
                "customer_login"
            )
        )

    products = read_json(
        "products.json"
    )

    if not isinstance(
        products,
        list
    ):
        products = []

    product = next(
        (
            p
            for p in products
            if (
                p.get(
                    "product_id"
                )
                == product_id
                and p.get(
                    "status"
                )
                == "published"
                and p.get(
                    "approval_status"
                )
                == "approved"
            )
        ),
        None
    )

    if product is None:

        return (
            "Product not found",
            404
        )

    customer_id = session.get(
        "customer_id"
    )

    customer_name = request.form.get(
        "customer_name",
        ""
    ).strip()

    customer_mobile = request.form.get(
        "customer_mobile",
        ""
    ).strip()

    customer_address = request.form.get(
        "customer_address",
        ""
    ).strip()

    # ---------------------------------------------------------------
    # QUANTITY
    # ---------------------------------------------------------------

    try:

        quantity = int(
            request.form.get(
                "quantity",
                "1"
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        quantity = 1

    quantity = max(
        1,
        min(
            quantity,
            10
        )
    )

    # ---------------------------------------------------------------
    # CUSTOMER VALIDATION
    # ---------------------------------------------------------------

    if not customer_name:

        return (
            "Please enter your name.",
            400
        )

    if (
        not customer_mobile
        or not customer_mobile.isdigit()
        or len(customer_mobile) != 10
    ):

        return (
            "Please enter a valid mobile number.",
            400
        )

    if not customer_address:

        return (
            "Please enter your delivery address.",
            400
        )

    # ---------------------------------------------------------------
    # PRICE
    # ---------------------------------------------------------------

    try:

        unit_price = float(
            product.get(
                "final_price",
                0
            ) or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        unit_price = 0

    total_price = (
        unit_price * quantity
    )

    # ---------------------------------------------------------------
    # READ ORDERS
    # ---------------------------------------------------------------

    orders = read_json(
        "orders.json"
    )

    if not isinstance(
        orders,
        list
    ):
        orders = []

    # ---------------------------------------------------------------
    # GENERATE SAFE ORDER ID
    # ---------------------------------------------------------------

    order_numbers = []

    for order in orders:

        order_id = str(
            order.get(
                "order_id",
                ""
            )
        )

        if order_id.startswith(
            "ORD"
        ):

            try:

                order_numbers.append(
                    int(
                        order_id[3:]
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

    next_order_number = (
        max(
            order_numbers,
            default=0
        ) + 1
    )

    order_id = (
        f"ORD{next_order_number:04d}"
    )

    # ---------------------------------------------------------------
    # CREATE ORDER
    # ---------------------------------------------------------------

    new_order = {

        "order_id": order_id,

        "customer_id": customer_id,

        "customer_name": customer_name,

        "customer_mobile": customer_mobile,

        "customer_address": customer_address,

        "product_id": product.get(
            "product_id"
        ),

        "product_name": product.get(
            "name",
            ""
        ),

        "artisan_id": product.get(
            "artisan_id"
        ),

        "artisan_name": product.get(
            "artisan_name",
            ""
        ),

        "quantity": quantity,

        "unit_price": unit_price,

        "total_price": total_price,

        "status": "placed",

        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    orders.append(
        new_order
    )

    write_json(
        "orders.json",
        orders
    )

    # ---------------------------------------------------------------
    # UPDATE CUSTOMER DETAILS
    # ---------------------------------------------------------------

    customers = read_json(
        "customers.json"
    )

    if not isinstance(
        customers,
        list
    ):
        customers = []

    for customer in customers:

        if (
            customer.get(
                "customer_id"
            )
            == customer_id
        ):

            customer["name"] = (
                customer_name
            )

            customer["mobile"] = (
                customer_mobile
            )

            customer["address"] = (
                customer_address
            )

            break

    write_json(
        "customers.json",
        customers
    )

    # ---------------------------------------------------------------
    # UPDATE SESSION
    # ---------------------------------------------------------------

    session["customer_name"] = (
        customer_name
    )

    session["customer_mobile"] = (
        customer_mobile
    )

    session["customer_address"] = (
        customer_address
    )

    session.pop(
        "pending_checkout_product_id",
        None
    )

    # ---------------------------------------------------------------
    # ORDER SUCCESS
    # ---------------------------------------------------------------

    return render_template(
        "customer/order_success.html",
        order=new_order,
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# CUSTOMER LOGIN
# ===========================================================================

@app.route(
    "/customer/login",
    methods=["GET", "POST"]
)
def customer_login():

    # ---------------------------------------------------------------
    # OPTIONAL PRODUCT ID
    #
    # This allows links such as:
    #
    # /customer/login?next_product=1
    #
    # ---------------------------------------------------------------

    next_product = request.args.get(
        "next_product",
        type=int
    )

    if next_product:

        session[
            "pending_checkout_product_id"
        ] = next_product

    # ---------------------------------------------------------------
    # LOGIN POST
    # ---------------------------------------------------------------

    if request.method == "POST":

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # -----------------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------------

        if not mobile or not password:

            return render_template(
                "customer/login.html",
                error=(
                    "Please enter mobile number "
                    "and password."
                )
            )

        if (
            not mobile.isdigit()
            or len(mobile) != 10
        ):

            return render_template(
                "customer/login.html",
                error=(
                    "Please enter a valid "
                    "10-digit mobile number."
                )
            )

        # -----------------------------------------------------------
        # READ CUSTOMERS
        # -----------------------------------------------------------

        customers = read_json(
            "customers.json"
        )

        if not isinstance(
            customers,
            list
        ):
            customers = []

        # -----------------------------------------------------------
        # FIND CUSTOMER
        # -----------------------------------------------------------

        matched_customer = None

        for customer in customers:

            if (
                str(
                    customer.get(
                        "mobile",
                        ""
                    )
                ).strip()
                == mobile
            ):

                matched_customer = customer
                break

        if not matched_customer:

            return render_template(
                "customer/login.html",
                error=(
                    "Mobile number is not registered."
                )
            )

        # -----------------------------------------------------------
        # CHECK PASSWORD
        # -----------------------------------------------------------

        stored_password_hash = (
            matched_customer.get(
                "password_hash",
                ""
            )
        )

        if not stored_password_hash:

            return render_template(
                "customer/login.html",
                error=(
                    "Customer account is invalid. "
                    "Please register again."
                )
            )

        if not check_password_hash(
            stored_password_hash,
            password
        ):

            return render_template(
                "customer/login.html",
                error="Incorrect password."
            )

        # -----------------------------------------------------------
        # CUSTOMER SESSION
        # -----------------------------------------------------------

        session[
            "customer_logged_in"
        ] = True

        session[
            "customer_id"
        ] = matched_customer.get(
            "customer_id"
        )

        session[
            "customer_mobile"
        ] = matched_customer.get(
            "mobile"
        )

        session[
            "customer_name"
        ] = matched_customer.get(
            "name",
            "Customer"
        )

        session[
            "customer_address"
        ] = matched_customer.get(
            "address",
            ""
        )

        # -----------------------------------------------------------
        # RETURN TO PENDING CHECKOUT
        # -----------------------------------------------------------

        pending_product_id = session.pop(
            "pending_checkout_product_id",
            None
        )

        if pending_product_id:

            return redirect(
                url_for(
                    "customer_checkout",
                    product_id=int(
                        pending_product_id
                    )
                )
            )

        # -----------------------------------------------------------
        # OTHERWISE CUSTOMER HOME
        # -----------------------------------------------------------

        return redirect(
            url_for(
                "customer_home"
            )
        )

    # ---------------------------------------------------------------
    # LOGIN PAGE
    # ---------------------------------------------------------------

    return render_template(
        "customer/login.html",
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# CUSTOMER REGISTER
# ===========================================================================

@app.route(
    "/customer/register",
    methods=["GET", "POST"]
)
def customer_register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        # -----------------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------------

        if (
            not name
            or not mobile
            or not address
            or not password
        ):

            return render_template(
                "customer/register.html",
                error=(
                    "Please fill all required fields."
                )
            )

        if (
            not mobile.isdigit()
            or len(mobile) != 10
        ):

            return render_template(
                "customer/register.html",
                error=(
                    "Please enter a valid "
                    "10-digit mobile number."
                )
            )

        if password != confirm_password:

            return render_template(
                "customer/register.html",
                error=(
                    "Passwords do not match."
                )
            )

        # -----------------------------------------------------------
        # READ CUSTOMERS
        # -----------------------------------------------------------

        customers = read_json(
            "customers.json"
        )

        if not isinstance(
            customers,
            list
        ):
            customers = []

        # -----------------------------------------------------------
        # DUPLICATE MOBILE
        # -----------------------------------------------------------

        for customer in customers:

            if (
                str(
                    customer.get(
                        "mobile",
                        ""
                    )
                ).strip()
                == mobile
            ):

                return render_template(
                    "customer/register.html",
                    error=(
                        "This mobile number "
                        "is already registered."
                    )
                )

        # -----------------------------------------------------------
        # CUSTOMER ID
        # -----------------------------------------------------------

        customer_numbers = []

        for customer in customers:

            customer_id = str(
                customer.get(
                    "customer_id",
                    ""
                )
            )

            if customer_id.startswith(
                "CUST"
            ):

                try:

                    customer_numbers.append(
                        int(
                            customer_id[4:]
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        next_customer_number = (
            max(
                customer_numbers,
                default=0
            ) + 1
        )

        customer_id = (
            f"CUST{next_customer_number:03d}"
        )

        # -----------------------------------------------------------
        # HASH PASSWORD
        # -----------------------------------------------------------

        password_hash = (
            generate_password_hash(
                password
            )
        )

        # -----------------------------------------------------------
        # CREATE CUSTOMER
        # -----------------------------------------------------------

        new_customer = {

            "customer_id": customer_id,

            "name": name,

            "mobile": mobile,

            "address": address,

            "password_hash": password_hash,

            "wishlist": [],

            "cart": [],

            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        customers.append(
            new_customer
        )

        write_json(
            "customers.json",
            customers
        )

        # -----------------------------------------------------------
        # LOGIN CUSTOMER
        # -----------------------------------------------------------

        session[
            "customer_logged_in"
        ] = True

        session[
            "customer_id"
        ] = customer_id

        session[
            "customer_mobile"
        ] = mobile

        session[
            "customer_name"
        ] = name

        session[
            "customer_address"
        ] = address

        # -----------------------------------------------------------
        # IMPORTANT:
        # If registration happened during Buy Now,
        # return to checkout.
        # -----------------------------------------------------------

        pending_product_id = session.pop(
            "pending_checkout_product_id",
            None
        )

        if pending_product_id:

            return redirect(
                url_for(
                    "customer_checkout",
                    product_id=int(
                        pending_product_id
                    )
                )
            )

        return redirect(
            url_for(
                "customer_home"
            )
        )

    return render_template(
        "customer/register.html",
        current_lang=session.get(
            "language",
            DEFAULT_LANGUAGE
        )
    )


# ===========================================================================
# ADMIN PLACEHOLDER
# ===========================================================================

@app.route("/admin")
def admin_placeholder():

    return (
        "Admin module coming soon.",
        200
    )


# ===========================================================================
# ERROR HANDLERS
# ===========================================================================

@app.errorhandler(413)
def request_entity_too_large(error):

    return jsonify({
        "success": False,
        "error": (
            "The uploaded photos are too large. "
            "Please use smaller images."
        ),
    }), 413


@app.errorhandler(404)
def page_not_found(error):

    return (
        "Page not found.",
        404
    )


@app.errorhandler(500)
def internal_server_error(error):

    app.logger.exception(
        "Internal server error"
    )

    return (
        "Something went wrong. "
        "Please try again.",
        500
    )


# ===========================================================================
# APPLICATION START
# ===========================================================================

if __name__ == "__main__":

    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )
