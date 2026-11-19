
def assess_financial_status(monthly_budget, institution_type, fee_status=None):
    """
    Simplified monthly-budget assessment.

    Private: Affordable when monthly budget >= LKR 100,000.
    Government: Listed as Free when recorded as free.
    Vocational/unknown: Needs Verification.
    """

    institution = str(institution_type or "").strip().lower()
    fee = str(fee_status or "").strip().lower()

    if "government" in institution:
        if "free" in fee or not fee:
            return "Listed as Free"
        return "Needs Verification"

    if "private" in institution:
        try:
            budget = float(monthly_budget)
        except (TypeError, ValueError):
            return "Monthly Budget Required"

        return (
            "Affordable"
            if budget >= 100000
            else "Not Affordable"
        )

    return "Needs Verification"


def assess_academic_status(original_status):
    """
    Student-friendly wording.
    These labels do not establish formal admission eligibility.
    """

    status = str(original_status or "").strip().lower()

    if "potential stream mismatch" in status:
        return "Recommended – Check Subject Requirements"

    if "not assessed" in status or "needs verification" in status:
        return "Recommended for Your Profile – Requirements to Be Confirmed"

    if "eligible" in status:
        return "Recommended – Admission Requirements Indicated"

    return "Recommended for Your Profile – Check Entry Requirements"

