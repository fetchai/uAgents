import os

import utils
from analyser import SafetyAnalyser, SafetySystem
from summariser import SafetySummariser


def main():
    directory_path = os.path.join(os.path.dirname(__file__), "sample_data")
    incident = utils.pick_random_call("sample_data/telephone-safe-1.txt")

    summariser = SafetySummariser()
    analyser = SafetyAnalyser(directory_path)

    safety_system = SafetySystem(summariser, analyser)
    assessment = safety_system.react_to_incident(incident)

    print(
        "This incident has been deemed:",
        str.upper(assessment[1]),
        "\nReason:",
        assessment[0].Summary,
    )
    if str.lower(assessment[1]) == "safe":
        print("==> User is safe to respond to this incident, please continue.")
    elif str.lower(assessment[1]) == "unsafe":
        print("==> User is NOT to respond to this, defences activated.")


if __name__ == "__main__":
    main()
