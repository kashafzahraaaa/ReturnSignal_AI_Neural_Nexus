
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


# Complaint categories only.
# Product categories are handled separately by the customer form.

TRAINING_DATA = {
    "Damaged Product": [
        "The mirror arrived broken.",
        "My mirror is cracked.",
        "The glass product was shattered.",
        "The product arrived physically damaged.",
        "My phone screen is broken.",
        "The bottle arrived crushed.",
        "The product has a broken part.",
        "The item was damaged during delivery.",
        "The product arrived smashed.",
        "The item is cracked and unusable."
    ],

    "Leakage / Spillage": [
        "The bottle is leaking from the cap.",
        "Liquid spilled inside the package.",
        "The container was not sealed properly.",
        "My shampoo bottle leaked during delivery.",
        "The product is dripping from the bottom.",
        "Oil spilled out of the container.",
        "My face wash is leaking.",
        "The face wash bottle leaked inside the parcel.",
        "The cream container is leaking.",
        "The liquid soap spilled during shipping."
    ],

    "Missing Items / Parts": [
        "Some items are missing from my order.",
        "I ordered three products but received only two.",
        "One item was missing from the parcel.",
        "My order is incomplete.",
        "The package contains fewer items than I paid for.",
        "My mirror was not included.",
        "I did not receive one of my products.",
        "Part of my order is missing.",
        "The parcel did not contain everything I ordered."
    ],

    "Wrong Product Delivered": [
        "I received a completely different product.",
        "The delivered item is not what I ordered.",
        "I ordered a black shirt but received a blue one.",
        "I received the wrong item.",
        "The wrong model was delivered.",
        "The package contains someone else's product.",
        "The wrong product variant was delivered."
    ],

    "Poor Product Quality": [
        "The product quality is very poor.",
        "The material feels cheap and low quality.",
        "The product is not worth the price.",
        "The product feels weak and poorly made.",
        "The item broke after very little use.",
        "The product does not meet quality expectations.",
        "The material is inferior.",
        "The product looks cheaply manufactured."
    ],

    "Defective / Not Working": [
        "The device does not turn on.",
        "The screen is not displaying anything.",
        "The electronic device keeps restarting.",
        "The buttons are not responding.",
        "The appliance stopped functioning.",
        "The machine does not work.",
        "The device overheats while operating.",
        "The product is defective.",
        "The display is flickering."
    ],

    "Damaged Packaging": [
        "The parcel arrived with a damaged box.",
        "The packaging was crushed during delivery.",
        "The package was torn when it arrived.",
        "The outer box was badly damaged.",
        "The seal on the package was broken.",
        "The parcel arrived open.",
        "The packaging was wet and ripped.",
        "The box was dented during shipping."
    ],

    "Expired Product": [
        "The product arrived after its expiry date.",
        "The food item is already expired.",
        "The expiry date printed on the package has passed.",
        "The product is past its use by date.",
        "I received an expired item.",
        "The product was already out of date."
    ],

    "Incorrect Product Description": [
        "The product does not match its online description.",
        "The advertised features are not available.",
        "The product description is misleading.",
        "The item is different from the pictures shown online.",
        "The advertised material does not match the delivered product."
    ],

    "Wrong Size / Quantity": [
        "The shoes are smaller than the size I ordered.",
        "I ordered a large size but received a small one.",
        "The product dimensions do not match.",
        "The delivered quantity is incorrect.",
        "The product capacity is lower than advertised.",
        "The measurements are not as described."
    ],

    "Delivery Delay": [
        "My order has not arrived on the promised date.",
        "The delivery is taking much longer than expected.",
        "My parcel is still delayed.",
        "The order has been stuck in transit for days.",
        "The delivery date keeps getting postponed.",
        "My package has not arrived yet."
    ],

    "Incorrect Delivery": [
        "My order was delivered to the wrong address.",
        "The delivery person gave my parcel to someone else.",
        "My package was sent to the wrong location.",
        "The order was delivered to another customer.",
        "The parcel was delivered to the wrong house."
    ],

    "Return / Refund Issue": [
        "I requested a refund but have not received it.",
        "My return request has not been processed.",
        "I returned the product but my money was not refunded.",
        "The refund is delayed.",
        "The seller is not accepting my return."
    ]
}


training_texts = []
training_labels = []

for category, examples in TRAINING_DATA.items():
    for example in examples:
        training_texts.append(example)
        training_labels.append(category)


model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1500,
            class_weight="balanced",
            random_state=42
        )
    )
])

model.fit(training_texts, training_labels)


def make_result(category, confidence, status, explanation):
    return {
        "category": category,
        "confidence": round(float(confidence), 4),
        "status": status,
        "explanation": explanation
    }


def classify_complaint(text):
    complaint = str(text or "").strip()
    normalized = re.sub(r"\s+", " ", complaint.lower())

    if not normalized:
        return make_result(
            "Unknown / Uncategorized",
            0,
            "unknown",
            "No complaint description was provided."
        )

    words = normalized.split()

    if len(words) < 2:
        return make_result(
            "Unknown / Uncategorized",
            0,
            "unknown",
            "The complaint contains too little information for reliable classification."
        )

    irrelevant_phrases = [
        "tell me a joke",
        "write me a poem",
        "what is the weather",
        "who are you",
        "what is your name",
        "solve my homework",
        "tell me a story",
        "good morning",
        "good evening",
        "hello there"
    ]

    if any(phrase in normalized for phrase in irrelevant_phrases):
        return make_result(
            "Unknown / Uncategorized",
            0,
            "irrelevant",
            "The submitted text does not appear to describe a product complaint."
        )

    # Specific rules take priority over machine-learning predictions.
    # More specific rules are checked before general rules.
    rules = [
        (
            r"\b(charger|adapter|remote|cable|manual|accessory|accessories)"
            r"\b.*\b(missing|absent|not included|not received)\b",
            "Missing Items / Parts"
        ),
        (
            r"\b(leak|leaks|leaking|leaked|spill|spills|spilled|spilling)\b",
            "Leakage / Spillage"
        ),
        (
            r"\b(expired|expiration|expiry|out of date)\b",
            "Expired Product"
        ),
        (
            r"\b(damaged packaging|damaged box|torn parcel|crushed box|"
            r"broken seal|ripped packaging|wet packaging)\b",
            "Damaged Packaging"
        ),
        (
            r"\b(wrong address|wrong location|wrong house|delivered to someone else)\b",
            "Incorrect Delivery"
        ),
        (
            r"\b(refund|refunded|return request|returned the product)\b",
            "Return / Refund Issue"
        ),
        (
            r"\b(delayed|delay|late delivery|not arrived|stuck in transit)\b",
            "Delivery Delay"
        ),
        (
            r"\b(wrong product|wrong item|different product|wrong model)\b",
            "Wrong Product Delivered"
        ),
        (
            r"\b(missing|not received|never received|not included|"
            r"wasn't included|was not included|absent|incomplete)\b",
            "Missing Items / Parts"
        ),
        (
            r"\b(cracked|broken|shattered|smashed|physically damaged)\b",
            "Damaged Product"
        ),
        (
            r"\b(not working|does not work|doesn't work|not turning on|"
            r"defective|stopped functioning|not functioning)\b",
            "Defective / Not Working"
        ),
        (
            r"\b(wrong size|incorrect size|size mismatch|wrong dimensions)\b",
            "Wrong Size / Quantity"
        ),
        (
            r"\b(description|advertised|misleading|product pictures)\b",
            "Incorrect Product Description"
        ),
        (
            r"\b(poor quality|low quality|cheap material|bad quality)\b",
            "Poor Product Quality"
        )
    ]

    for pattern, category in rules:
        if re.search(pattern, normalized):
            return make_result(
                category,
                0.90,
                "classified",
                f"The complaint matched a specific {category.lower()} recognition rule."
            )

    probabilities = model.predict_proba([normalized])[0]
    categories = model.named_steps["classifier"].classes_

    ranked = sorted(
        zip(categories, probabilities),
        key=lambda item: item[1],
        reverse=True
    )

    predicted_category, confidence = ranked[0]
    second_confidence = ranked[1][1] if len(ranked) > 1 else 0

    confidence_threshold = 0.38
    margin_threshold = 0.07

    if confidence < confidence_threshold or (
        confidence - second_confidence < margin_threshold
    ):
        return make_result(
            "Other / New Complaint",
            confidence,
            "needs_review",
            "The AI could not confidently match this complaint to an existing category. "
            "It has been placed in Other / New Complaint for human review."
        )

    return make_result(
        predicted_category,
        confidence,
        "classified",
        f"The AI identified this complaint as {predicted_category} "
        "based on the complaint description."
    )
