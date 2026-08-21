from scripts.sft.pass_at_8_eval import programmatic_judge


def test_financial_ocr_ignores_presentation_only_number_formatting():
    assert programmatic_judge(
        "128,560.00元",
        "128560",
        task="financial_ocr",
    ) is True
    assert programmatic_judge(
        "83.38美元/桶",
        "83.38",
        task="financial_ocr",
    ) is True


def test_financial_ocr_keeps_value_and_percent_semantics_strict():
    assert programmatic_judge(
        "128,560.00元",
        "128000",
        task="financial_ocr",
    ) is False
    assert programmatic_judge(
        "5.00%",
        "5",
        task="financial_ocr",
    ) is False
    assert programmatic_judge(
        "5.00%",
        "5.0%",
        task="financial_ocr",
    ) is True


def test_entity_extraction_json_is_order_and_key_order_insensitive():
    reference = '[{"entity":"甲公司","type":"ORG"},{"entity":"张三","type":"PERSON"}]'
    candidate = '''```json
[
  {"type": "PERSON", "entity": "张三"},
  {"type": "ORG", "entity": "甲公司"}
]
```'''
    assert programmatic_judge(
        reference,
        candidate,
        task="financial_entity_extraction",
    ) is True


def test_entity_extraction_still_requires_complete_exact_set():
    reference = '[{"entity":"甲公司","type":"ORG"},{"entity":"张三","type":"PERSON"}]'
    missing = '[{"entity":"甲公司","type":"ORG"}]'
    wrong_type = '[{"entity":"甲公司","type":"ORG"},{"entity":"张三","type":"ORG"}]'
    extra = '[{"entity":"甲公司","type":"ORG"},{"entity":"张三","type":"PERSON"},{"entity":"李四","type":"PERSON"}]'

    for candidate in (missing, wrong_type, extra):
        assert programmatic_judge(
            reference,
            candidate,
            task="financial_entity_extraction",
        ) is False
