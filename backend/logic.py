# logic.py
# Core screening logic for EarlySteps

def evaluate_screening(answers):
    """
    Evaluate developmental screening based on observed behaviors.
    """

    if not answers or not isinstance(answers, list):
        return (
            "Invalid Input",
            "No screening data received."
        )

    missing_count = 0
    for answer in answers:
        if answer is False:
            missing_count += 1

    if missing_count <= 1:
        return (
            "On Track",
            "Most age-appropriate behaviors were observed. Continue routine monitoring."
        )
    elif 2 <= missing_count <= 3:
        return (
            "Needs Monitoring",
            "Some age-appropriate behaviors were not observed. Monitoring is recommended."
        )
    else:
        return (
            "Extra Support Recommended",
            "Several age-appropriate behaviors were not observed. Consider consulting a professional."
        )
