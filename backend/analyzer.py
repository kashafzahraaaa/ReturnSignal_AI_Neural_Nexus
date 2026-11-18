
from collections import Counter, defaultdict


UNKNOWN_LABEL = "Unknown / Uncategorized"
OTHER_COMPLAINT = "Other / New Complaint"
OTHER_PRODUCT = "Other Product Category"


UNKNOWN_COMPLAINT_CATEGORIES = {
    UNKNOWN_LABEL,
    "Unknown / Unclear Reasons",
    "Uncategorized"
}

UNKNOWN_PRODUCT_CATEGORIES = {
    UNKNOWN_LABEL,
    "Uncategorized",
    ""
}


def analyze_records(records):
    # Total includes every submitted record, including irrelevant entries.
    total = len(records)

    # Exclude irrelevant text from operational analysis.
    valid = [
        row for row in records
        if str(row.get("status", "")).lower() != "irrelevant"
    ]

    product_counts = Counter()
    complaint_category_counts = Counter()
    product_category_counts = Counter()

    product_categories = defaultdict(Counter)
    product_type_breakdown = defaultdict(Counter)

    daily_counts = Counter()
    sentiments = Counter()

    unknown_complaint_count = 0
    unknown_product_count = 0
    other_complaint_count = 0
    high_severity = 0

    for row in valid:
        product = str(
            row.get("product") or "Unspecified Product"
        ).strip()

        complaint_category = str(
            row.get("category") or UNKNOWN_LABEL
        ).strip()

        product_category = str(
            row.get("product_category") or UNKNOWN_LABEL
        ).strip()

        date = str(row.get("date") or "")[:10]

        # Product name analysis.
        product_counts[product] += 1

        # Complaint category analysis.
        complaint_category_counts[complaint_category] += 1

        # Product category analysis.
        product_category_counts[product_category] += 1

        # Relationship between individual products and complaint types.
        product_categories[product][complaint_category] += 1

        # Relationship between product categories and product names.
        product_type_breakdown[product_category][product] += 1

        if complaint_category in UNKNOWN_COMPLAINT_CATEGORIES:
            unknown_complaint_count += 1

        if product_category in UNKNOWN_PRODUCT_CATEGORIES:
            unknown_product_count += 1

        if complaint_category == OTHER_COMPLAINT:
            other_complaint_count += 1

        if str(row.get("severity", "")).lower() == "high":
            high_severity += 1

        if date:
            daily_counts[date] += 1

        text = str(row.get("complaint_text", "")).lower()

        if any(word in text for word in [
            "bad", "poor", "broken", "disappointed",
            "defective", "damaged", "leak", "missing"
        ]):
            sentiments["Negative"] += 1

        elif any(word in text for word in [
            "good", "great", "excellent", "love"
        ]):
            sentiments["Positive"] += 1

        else:
            sentiments["Neutral / Unclear"] += 1

    # Ranking by individual product name.
    product_ranking = [
        {
            "product": name,
            "complaints": count
        }
        for name, count in product_counts.most_common()
    ]

    # Ranking by complaint category.
    category_ranking = [
        {
            "category": name,
            "complaints": count
        }
        for name, count in complaint_category_counts.most_common()
    ]

    # Ranking by product category.
    product_category_ranking = [
        {
            "category": name,
            "complaints": count
        }
        for name, count in product_category_counts.most_common()
    ]

    # Individual products and their complaint categories.
    product_breakdown = []

    for product, categories in product_categories.items():
        product_breakdown.append({
            "product": product,
            "complaints": sum(categories.values()),
            "categories": [
                {
                    "category": name,
                    "complaints": count
                }
                for name, count in categories.most_common()
            ]
        })

    # Product categories and the products belonging to each category.
    product_category_breakdown = []

    for product_category, products in product_type_breakdown.items():
        product_category_breakdown.append({
            "category": product_category,
            "complaints": sum(products.values()),
            "products": [
                {
                    "product": name,
                    "complaints": count
                }
                for name, count in products.most_common()
            ]
        })

    unknown_rate = (
        round(
            (unknown_complaint_count / len(valid)) * 100,
            1
        )
        if valid else 0
    )

    sorted_dates = sorted(daily_counts.items())

    daily_trend = [
        {
            "date": date,
            "complaints": count
        }
        for date, count in sorted_dates
    ]

    # Detect unusual increases in daily complaint volume.
    anomalies = []

    recent_values = [
        count for _, count in sorted_dates[-7:]
    ]

    if len(recent_values) >= 4:
        baseline_values = recent_values[:-1]
        baseline = sum(baseline_values) / len(baseline_values)
        latest = recent_values[-1]

        if baseline > 0 and latest >= baseline * 2:
            anomalies.append({
                "title": "Unusual complaint increase",
                "description": (
                    "The latest recorded day has at least twice "
                    "the average complaints of the preceding days."
                ),
                "severity": "High"
            })

    return {
        "total": total,
        "products_count": len(product_counts),
        "categories_count": len(complaint_category_counts),

        # Complaint classification metrics.
        "unknown_count": unknown_complaint_count,
        "unknown_complaint_count": unknown_complaint_count,
        "other_complaint_count": other_complaint_count,
        "unknown_rate": unknown_rate,

        # Product classification metrics.
        "unknown_product_count": unknown_product_count,
        "product_categories_count": len(product_category_counts),

        "high_severity": high_severity,

        # Rankings for dashboard charts.
        "product_ranking": product_ranking,
        "category_ranking": category_ranking,
        "complaint_category_ranking": category_ranking,
        "product_category_ranking": product_category_ranking,

        # Detailed breakdowns.
        "product_breakdown": product_breakdown,
        "product_category_breakdown": product_category_breakdown,

        "daily_trend": daily_trend,
        "sentiment": dict(sentiments),
        "anomalies": anomalies
    }


def root_cause_analysis(records):
    results = []
    product_groups = defaultdict(list)

    for row in records:
        if str(row.get("status", "")).lower() == "irrelevant":
            continue

        product = row.get("product") or "Unspecified Product"
        product_groups[product].append(row)

    hypotheses = {
        "Damaged Product":
            "Possible supplier quality, handling, or product protection issue.",

        "Leakage / Spillage":
            "Possible packaging seal, container, or handling issue.",

        "Missing Items / Parts":
            "Possible packing checklist or warehouse fulfilment issue.",

        "Wrong Product Delivered":
            "Possible order picking, packing, or product-labelling error.",

        "Poor Product Quality":
            "Possible supplier quality or manufacturing issue.",

        "Defective / Not Working":
            "Possible manufacturing, testing, or component issue.",

        "Damaged Packaging":
            "Possible packaging or transportation handling issue.",

        "Expired Product":
            "Possible inventory rotation, storage, or expiry-check issue.",

        "Incorrect Product Description":
            "Possible product listing or catalogue information issue.",

        "Wrong Size / Quantity":
            "Possible product specification or order fulfilment issue.",

        "Delivery Delay":
            "Possible shipping, dispatch, or logistics issue.",

        "Incorrect Delivery":
            "Possible address verification or delivery routing issue.",

        "Return / Refund Issue":
            "Possible returns processing or refund workflow issue.",

        "Other / New Complaint":
            "Further investigation is required to identify the operational cause.",

        "Unknown / Uncategorized":
            "Insufficient complaint details. Further review is required."
    }

    for product, rows in product_groups.items():
        counts = Counter(
            row.get("category") or UNKNOWN_LABEL
            for row in rows
        )

        if not counts:
            continue

        category, count = counts.most_common(1)[0]

        # Determine the product category associated with this product.
        product_category_counts = Counter(
            row.get("product_category") or UNKNOWN_LABEL
            for row in rows
        )

        product_category = product_category_counts.most_common(1)[0][0]

        results.append({
            "product": product,
            "product_category": product_category,
            "leading_category": category,
            "complaints": count,
            "likely_cause": hypotheses.get(
                category,
                "Further investigation is required to identify the cause."
            ),
            "evidence": (
                f"{count} of {len(rows)} recorded complaints "
                f"for this product fall into this category."
            ),
            "confidence_label":
                "Initial hypothesis — requires human verification"
        })

    return sorted(
        results,
        key=lambda item: item["complaints"],
        reverse=True
    )
