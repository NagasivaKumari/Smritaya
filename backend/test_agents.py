from agents import extract_deeds, _map_deed, _unwrap_deeds, _normalize_memo

CASES = {
    "Bhai wardrobe Sunday tak complete ho jayega pakka, total eight thousand rupees lagega.": 8000,
    "Advance mil gaya hai, Wednesday tak ceiling leakage repair electrician theek kar dega, tension mat lo.": None,
    "Emergency ke liye 25,000 transfer kar de bhai, next month salary aate hi pakka clear kar dunga.": 25000,
    "Deliver the brand guidelines on Monday and we will release the remaining forty thousand immediately.": 40000,
}

for text, amount in CASES.items():
    deeds = extract_deeds(text)
    assert deeds, f"no deed: {text}"
    assert deeds[0]["amount"] == amount, f"{text!r} -> {deeds[0]['amount']} != {amount}"
    assert deeds[0]["due_ts"], f"no due date: {text}"

# dynamic field names: users may name their Studio schema fields freely
alt = {"person": "Ramesh", "words": "wardrobe by Sunday", "value": "8,000",
       "deadline": "2026-10-18", "owes": "i_owe", "category": "carpentry",
       "venue": "shop", "witness": "Anita"}
m = _map_deed(alt)
assert m["counterparty"] == "Ramesh"
assert m["quote"] == "wardrobe by Sunday"
assert m["amount"] == 8000.0
assert m["direction"] == "i_owe"
assert m["topic"] == "carpentry"
assert m["due_ts"] is not None
assert m["extra"] == {"venue": "shop", "witness": "Anita"}, "extra fields must not be dropped"

# catch-all bag is flattened, not left nested — accepts dict OR [{key,value}] (strict form)
d2 = _map_deed({"quote": "pay rent", "details": {"property": "Flat 3B", "landlord_phone": "999"}})
assert d2["extra"] == {"property": "Flat 3B", "landlord_phone": "999"}, d2["extra"]
d3 = _map_deed({"quote": "pay rent", "details": [{"key": "property", "value": "Flat 3B"}, {"key": "landlord_phone", "value": "999"}]})
assert d3["extra"] == {"property": "Flat 3B", "landlord_phone": "999"}, d3["extra"]

assert _unwrap_deeds({"commitments": [alt]}) == [alt]
assert _unwrap_deeds(alt) == [alt]
memo = _normalize_memo({"hearing_memo": {"opening": "A", "demand": "B", "legal_notice": "C"}})
assert memo["summons"] == "A" and memo["firm"] == "B" and memo["formal"] == "C"

print("ok", len(CASES), "cases + dynamic mapping")
