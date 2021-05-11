import json
# Load data
def load_data():
    with open("source/old/data/identifier_predicates.json", "r") as data:
        identifier_predicates = json.load(data)  # Identifiers and predicates

    with open("source/old/data/label_dict.json", "r") as data:
        label_dict = json.load(data)  # Label dictionary

    with open("source/old/data/predicate_frequencies_dict.json", "r") as data:
        predicate_frequencies_dict = json.load(data)  # Predicate frequency

    with open("source/old/data/entity_frequencies_dict.json", "r") as data:
        entity_frequencies_dict = json.load(data)  # Entity frequency

    with open("source/old/data/statements_dict.json", "r") as data:
        statements_dict = json.load(data)
    return identifier_predicates, label_dict, predicate_frequencies_dict, entity_frequencies_dict, statements_dict