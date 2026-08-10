from scripts.data.select_benchmark_aligned_tasks import (
    CAPABILITIES,
    Candidate,
    _content_hash,
    _load_candidate_cache,
    _parse_named_input,
    _select_capability,
    _scan_inputs,
    assess_all,
    assess_row,
    review_alignment,
    select_modality_quota,
    select_top,
)


def _row(question, answer, *, task="drifted_label", images=None, split="train"):
    row = {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "task": task,
        "split": split,
    }
    if images is not None:
        row["images"] = images
    return row


def test_label_alone_cannot_make_a_row_match():
    row = _row(
        "Translate this sentence into English.",
        "The weather is good today.",
        task="risk_sentiment_policy",
    )

    decision = assess_row(row, "risk_sentiment_policy")

    assert not decision.accepted


def test_content_can_match_despite_drifted_label():
    row = _row(
        "<image>根据图中的资金流向和指数走势，可能存在哪些市场风险？",
        "资金持续净流出，可能带来流动性风险、价格波动风险和市场情绪恶化。",
        task="chart_qa",
        images=["missing/risk.png"],
    )

    decision = assess_row(row, "risk_sentiment_policy")

    assert decision.accepted
    assert "risk_identification" == decision.subtype


def test_split_and_image_existence_do_not_affect_decision():
    train_row = _row(
        "<image>根据图中RSI指标走势，给出交易建议。",
        "当前接近超卖区，可等待反转确认后分批买入，并设置止损。",
        images=["definitely/not/present.png"],
        split="test",
    )
    other_row = dict(train_row, split="validation")

    first = assess_row(train_row, "investment_advice_strategy")
    second = assess_row(other_row, "investment_advice_strategy")

    assert first.accepted
    assert second.accepted
    assert first.score == second.score


def test_basic_arithmetic_requires_financial_calculation_content():
    positive = _row(
        "某公司收入由100万元增长至121万元，请计算两年复合增长率。公式为(现值/基值)^(1/年数)-1。",
        "复合增长率为10%。",
    )
    negative = _row(
        "公司今年收入增长较快，请评价其经营表现。",
        "公司的经营表现有所改善。",
        task="basic_arithmetic_metrics",
    )

    assert assess_row(positive, "basic_arithmetic_metrics").accepted
    assert not assess_row(negative, "basic_arithmetic_metrics").accepted


def test_candlestick_requires_technical_time_series_content():
    positive = _row(
        "<image>请识别这张K线图中的V型底，并分析成交量变化。",
        "股价快速下跌后反弹形成V型底，反弹阶段成交量放大。",
        images=["missing/kline.png"],
    )
    negative = _row(
        "<image>柱状图中哪个国家的销售额最高？",
        "中国最高。",
        task="candlestick_time_series",
        images=["missing/bar.png"],
    )

    assert assess_row(positive, "candlestick_time_series").accepted
    assert not assess_row(negative, "candlestick_time_series").accepted


def test_image_caption_requires_holistic_description_intent():
    positive = _row(
        "<image>请概述图片展示的主要内容。",
        "图片展示股票交易界面，包括价格走势、成交量、资金流向和主要盘口指标。",
        images=["missing/screen.png"],
    )
    negative = _row(
        "<image>图中2023年的收入是多少？",
        "2023年的收入为10亿元。",
        task="image_caption",
        images=["missing/chart.png"],
    )

    assert assess_row(positive, "image_caption").accepted
    assert not assess_row(negative, "image_caption").accepted


def test_causal_explanation_requires_cause_and_financial_context():
    positive = _row(
        "<image>为什么该公司净利润连续两年大幅下降？",
        "主要由于收入下降、原材料成本上升以及资产减值增加。",
        images=["missing/profit.png"],
    )
    negative = _row(
        "为什么天空是蓝色的？",
        "由于瑞利散射。",
        task="explanation_anomaly_causality",
    )

    assert assess_row(positive, "explanation_anomaly_causality").accepted
    assert not assess_row(negative, "explanation_anomaly_causality").accepted


def test_multimodal_financial_knowledge_requires_image_and_financial_concept():
    positive = _row(
        "<image>图中的内盘和外盘分别是什么意思？",
        "内盘是主动卖盘，外盘是主动买盘，可用于观察买卖力量。",
        images=["missing/quote.png"],
    )
    no_image = _row(
        "内盘和外盘分别是什么意思？",
        "内盘是主动卖盘，外盘是主动买盘。",
        task="multimodal_financial_knowledge",
    )

    assert assess_row(positive, "multimodal_financial_knowledge").accepted
    assert not assess_row(no_image, "multimodal_financial_knowledge").accepted


def test_image_grounded_explanation_prompt_matches_financial_knowledge():
    row = _row(
        "<image>Explain how the BOLL indicator is used in stock trading.",
        "BOLL bands describe price volatility and relative position; traders watch band contraction, expansion, and price crossings for possible signals.",
        images=["missing/boll.png"],
    )

    assert assess_row(row, "multimodal_financial_knowledge").accepted


def test_image_grounded_financial_indicator_interpretation_matches_knowledge():
    row = _row(
        "<image>What does the widening gap between M1 and M2 indicate about market liquidity?",
        "It indicates that broad liquidity is growing faster than transaction money, reflecting weaker corporate activity and more funds remaining in savings or financial assets.",
        images=["missing/liquidity.png"],
    )

    assert assess_row(row, "multimodal_financial_knowledge").accepted


def test_image_grounded_financial_concept_exam_does_not_match_explanation_benchmark():
    row = _row(
        "<image>Which aspects of a country's demographics does a dependency ratio inform? A: Population age structure B: Economic burden C: Labor force potential",
        "ABC",
        images=["missing/demographics.png"],
    )

    decision = assess_row(row, "multimodal_financial_knowledge")

    assert not decision.accepted


def test_image_grounded_chart_lookup_exam_is_not_financial_knowledge():
    row = _row(
        "<image>Which year shows the highest revenue? A: 2020 B: 2021 C: 2022 D: 2023",
        "D",
        images=["missing/revenue.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_qualitative_financial_exam_does_not_match_explanation_benchmark():
    row = _row(
        "<image>Which of the following statements best describes how higher credit spreads affect bond risk? A: Risk falls B: Risk rises C: No relationship D: Prices always rise",
        "B",
        images=["missing/spread.png"],
    )

    decision = assess_row(row, "multimodal_financial_knowledge")

    assert not decision.accepted


def test_compliance_matches_rule_application_not_generic_legal_text():
    positive = _row(
        "依据材料判断该投资机构是否符合GIPS合规要求，并选择正确答案。",
        "A",
        images=["missing/gips.png"],
    )
    negative = _row(
        "概括这份普通租赁合同。",
        "这是一份房屋租赁合同。",
        task="compliance_safety_suitability",
        images=["missing/lease.png"],
    )

    assert assess_row(positive, "compliance_safety_suitability").accepted
    assert not assess_row(negative, "compliance_safety_suitability").accepted


def test_assess_all_matches_individual_assessment():
    row = _row(
        "<image>根据图中的资金流向，可能存在哪些市场风险？",
        "可能存在流动性风险和价格波动风险。",
        images=["missing/risk.png"],
    )

    decisions = assess_all(row)

    assert decisions["risk_sentiment_policy"] == assess_row(row, "risk_sentiment_policy")


def test_text_financial_risk_analysis_does_not_match_image_benchmark():
    row = _row(
        "请依据以下财务披露识别主要风险、风险等级、影响路径和关键指标。",
        "风险等级为高，主要是供应链中断风险，影响路径是原料短缺导致收入下降。",
        task="financial_sentiment_analysis",
    )

    decision = assess_row(row, "risk_sentiment_policy")

    assert not decision.accepted


def test_text_evidence_based_investment_advice_does_not_match_image_benchmark():
    row = _row(
        "根据该公司的盈利、估值和负债情况，投资者应当如何操作？",
        "建议暂时观望；若估值回落且盈利改善可分批买入，并设置止损。",
    )

    decision = assess_row(row, "investment_advice_strategy")

    assert not decision.accepted


def test_english_personal_investment_decision_without_image_is_rejected():
    row = _row(
        "Is it prudent to sell a volatile stock after a 40% rise in two months?",
        "I would consider taking part of the profit, diversifying the proceeds, and keeping a stop loss on the remainder.",
    )

    decision = assess_row(row, "investment_advice_strategy")

    assert not decision.accepted


def test_high_risk_investment_search_without_image_is_rejected():
    row = _row(
        "How can I find a high-risk, high-reward investment that is diversified from the U.S. economy?",
        "Consider a small allocation to diversified emerging-market assets, avoid concentration, and size the position according to your risk tolerance.",
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_should_i_choose_investment_product_without_image_is_rejected():
    row = _row(
        "Should I choose a dividend ETF or an individual stock for a diversified portfolio?",
        "Consider the diversified ETF if you want lower concentration risk; use individual stocks only with smaller position sizes and adequate research.",
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_evidence_based_market_forecast_matches_benchmark_trend_subtype():
    row = _row(
        "<image>Based on the supplied chart, provide an analysis and prediction for the company's stock price movement next week.",
        "Prediction: moderately bullish. Analysis: revenue improved and demand strengthened, although valuation and policy risks remain.",
        images=["missing/forecast.png"],
    )

    decision = assess_row(row, "investment_advice_strategy")

    assert decision.accepted
    assert decision.subtype == "evidence_based_market_forecast"


def test_text_investment_strategy_application_does_not_match_visual_benchmark():
    row = _row(
        "How does value averaging work in practice for a portfolio of stocks and cash?",
        "Set a target portfolio value path, buy more stocks when the portfolio falls below it, and move money to cash when it rises above it. This requires periodic rebalancing.",
    )

    decision = assess_row(row, "investment_advice_strategy")

    assert not decision.accepted


def test_cause_selection_with_identifier_answer_is_not_explanatory_capability():
    row = _row(
        "从下列新闻中识别哪些内容导致该公司股票大涨。候选内容为1、2、3、4。",
        "1, 4",
    )

    assert not assess_row(row, "explanation_anomaly_causality").accepted


def test_financial_causal_chain_ordering_does_not_match_visual_explanation():
    row = _row(
        "Sort the following financial events into causal order: 1. demand falls 2. revenue declines 3. the company cuts investment.",
        "1,2,3",
    )

    decision = assess_row(row, "explanation_anomaly_causality")

    assert not decision.accepted


def test_financial_impact_path_without_image_does_not_match_visual_explanation():
    row = _row(
        "What is the impact of higher funding costs on the company's profitability and growth?",
        "Higher interest expense compresses profit margins and reduces cash available for investment, which can slow growth.",
    )

    decision = assess_row(row, "explanation_anomaly_causality")

    assert not decision.accepted


def test_text_technical_analysis_does_not_match_visual_candlestick_benchmark():
    row = _row(
        "股价突破BOLL中轨且成交量放大通常意味着什么？",
        "这通常表示上涨趋势得到确认，但仍应结合止损和后续量价变化判断。",
    )

    decision = assess_row(row, "candlestick_time_series")

    assert not decision.accepted


def test_technical_analysis_concept_without_chart_is_rejected():
    row = _row(
        "Please answer this professional technical analysis trading question. Context: Define tick volume and explain why traders use it as a substitute for actual intraday volume.",
        "Tick volume counts price changes during a period and tracks market activity, so it can approximate unavailable real-time exchange volume.",
    )

    decision = assess_row(row, "candlestick_time_series")

    assert not decision.accepted


def test_candlestick_concept_exam_without_chart_is_rejected():
    row = _row(
        "You are solving a task on the topic 'Chart Construction'. Context: On a candlestick chart, what does the real body show? A: Open-close distance B: Volume C: Market cap D: Dividend yield",
        "A",
    )

    decision = assess_row(row, "candlestick_time_series")

    assert not decision.accepted


def test_dialogue_matching_with_incidental_technical_terms_is_not_candlestick():
    row = _row(
        "# Task Objective: identify which dialogue each description comes from. ## Dialogue 1 Human: Explain the RSI and moving average stock trend. ## Descriptions: match item 1.",
        '[{"description_id":1,"answer":[1]}]',
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_university_multi_hop_question_does_not_match_rsi_substring():
    row = _row(
        "Answer the multi-hop question using the supplied documents. Documents: University College provides finance and market physics programmes.",
        "The evidence states that the university provides physics programmes.",
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_data_verification_with_market_columns_is_not_candlestick():
    row = _row(
        "You are a data verification expert. Verify each description id and identify data errors. Number: 1 Query: stock volume and price trend.",
        "[1,2]",
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_text_compliance_rule_application_matches_core_capability():
    row = _row(
        "依据监管材料判断该投资机构是否符合信息披露义务。",
        "该机构不符合要求，因为规则要求在五个工作日内完成披露。",
    )

    assert assess_row(row, "compliance_safety_suitability").accepted


def test_english_overview_prompt_matches_image_caption():
    row = _row(
        "<image>Provide an overview of the information presented in this financial chart.",
        "The chart shows revenue and profit trends over five years, with revenue rising steadily while profit declines in the final year.",
        images=["missing/chart.png"],
    )

    assert assess_row(row, "image_caption").accepted


def test_sentiment_json_is_not_causal_explanation():
    row = _row(
        "标题：公司净利润大幅下降。正文包含公司经营情况，请完成情感标注。",
        '[{"ins_name":"某公司","sentiment_level":"-1","label_type":"财务指标"}]',
        task="explanation_anomaly_causality",
    )

    assert not assess_row(row, "explanation_anomaly_causality").accepted


def test_numeric_change_question_is_not_financial_concept_explanation():
    row = _row(
        "<image>What is the year-on-year change in FinTech revenue?",
        "101355 - 73138 = 28217 million.",
        task="multimodal_financial_knowledge",
        images=["missing/table.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_ranked_bank_lookup_is_not_financial_concept_knowledge():
    row = _row(
        "<image>What is the 14th largest bank in Europe?",
        "The 14th largest bank is Intesa Sanpaolo.",
        images=["missing/bank-rank.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_chart_multiple_choice_lookup_is_not_financial_concept_knowledge():
    row = _row(
        "<image>Which quarter had the highest cost-to-income ratio? A. 1Q B. 2Q C. 3Q D. 4Q",
        "C",
        images=["missing/ratio-chart.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_financial_analyst_table_analysis_is_not_concept_knowledge():
    row = _row(
        "<image>你是一个金融分析师，请根据图中三年的收入、成本和费用数据进行杜邦分析，并解释净资产收益率变化。",
        "销售利润率下降导致净资产收益率承压，资产周转率改善只能部分抵消该影响。",
        images=["missing/dupont.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_generic_document_ocr_is_not_financial_knowledge():
    row = _row(
        "<image>What is the title of this book?",
        "Common Core English.",
        task="multimodal_financial_knowledge",
        images=["missing/book.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_regulatory_obligation_question_is_not_risk_identification():
    row = _row(
        "依据监管材料回答：Authorised Persons应如何处理key person risk？",
        "机构必须建立信息安全政策并保存相关记录。",
        task="risk_sentiment_policy",
    )

    assert not assess_row(row, "risk_sentiment_policy").accepted


def test_event_extraction_is_not_investment_advice_or_arithmetic():
    row = _row(
        "从以下增持公告中抽取金融事件及其字段，公司拟买入100万股。",
        '[[0,"EquityOverweight",{"TradedShares":"100万股"}]]',
        task="investment_advice_strategy",
    )

    assert not assess_row(row, "investment_advice_strategy").accepted
    assert not assess_row(row, "basic_arithmetic_metrics").accepted


def test_generic_event_disclosure_is_not_compliance_application():
    row = _row(
        "从以下公告中抽取事件。董事会保证信息披露真实准确，并按监管要求履行义务。",
        '[[0,"EquityUnderweight",{"Holder":"张三"}]]',
        task="compliance_safety_suitability",
        images=["missing/notice.png"],
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_causal_ordering_template_is_not_compliance_application():
    row = _row(
        "Task Requirements: Sort these financial compliance events into causal order. 1. A rule changes 2. The company updates controls.",
        "1,2",
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_mae_yes_no_contract_question_is_not_causal_explanation():
    row = _row(
        "Question: MAE forward-looking standard (Y/N). Contract: Material Adverse Effect means any event reasonably expected to cause a decline.",
        "Yes",
    )

    assert not assess_row(row, "explanation_anomaly_causality").accepted


def test_hedge_accounting_recognition_is_not_investment_strategy():
    row = _row(
        "How are gains and losses excluded from the hedging relationship recognized?",
        "They are recognized prospectively in selling, general and administrative expenses.",
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_visual_financial_mechanism_matches_mixed_compliance_benchmark():
    row = _row(
        "<image>什么是沪股通？",
        "沪股通允许符合条件的境外投资者通过香港市场买卖上海证券交易所上市股票。",
        images=["missing/connect.png"],
    )

    decision = assess_row(row, "compliance_safety_suitability")

    assert decision.accepted
    assert decision.subtype == "benchmark_financial_mechanism"


def test_company_business_explanation_matches_mixed_compliance_benchmark():
    row = _row(
        "<image>请简要介绍图中英伟达公司的主营业务。",
        "英伟达主营GPU、数据中心计算、人工智能加速和专业可视化业务。",
        images=["missing/nvidia.png"],
    )

    decision = assess_row(row, "compliance_safety_suitability")

    assert not decision.accepted


def test_long_specific_chart_answer_is_not_holistic_image_caption():
    row = _row(
        "<image>Which year has the highest revenue?",
        "The bar chart displays annual revenue from 2019 through 2023. The horizontal axis lists the years and the vertical axis gives revenue in millions. Revenue rises each year, with 2023 represented by the tallest bar at 500 million.",
        images=["missing/revenue.png"],
    )

    decision = assess_row(row, "image_caption")

    assert not decision.accepted


def test_short_visual_answer_does_not_support_image_caption():
    row = _row(
        "<image>Which year has the highest revenue?",
        "2023.",
        task="image_caption",
        images=["missing/revenue.png"],
    )

    assert not assess_row(row, "image_caption").accepted


def test_generic_kline_overview_matches_candlestick_capability():
    row = _row(
        "<image>请概述一下这张图。",
        "这是一张股票K线走势图，包含开盘价、收盘价、均线和成交量；价格先下跌后反弹。",
        images=["missing/kline.png"],
    )

    assert assess_row(row, "candlestick_time_series").accepted


def test_stock_article_with_incidental_indicator_word_is_not_candlestick_task():
    row = _row(
        "阅读公司新闻并判断其情感倾向。新闻提到股价下跌和成交量变化。",
        "negative",
        task="candlestick_time_series",
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_generic_stock_forecast_is_not_candlestick_analysis():
    row = _row(
        "What do you think of this stock?",
        "The stock may rise because demand improved and trading volume increased, though market risk remains.",
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_text_stock_direction_forecast_is_not_candlestick_analysis():
    row = _row(
        "Based on the supplied news and financials, predict the company's stock price movement for the upcoming week.",
        "Prediction: moderately bullish. Improving demand supports a rise, although valuation risk remains.",
    )

    decision = assess_row(row, "candlestick_time_series")

    assert not decision.accepted


def test_text_market_time_series_forecast_is_not_candlestick_analysis():
    row = _row(
        "Based on the supplied weekly financial series, predict the company's stock price movement next week.",
        "Prediction: moderately bullish. The recent series shows improving returns and lower volatility, although downside risk remains.",
    )

    decision = assess_row(row, "candlestick_time_series")

    assert not decision.accepted


def test_high_to_current_price_drop_matches_candlestick_benchmark():
    row = _row(
        "<image>这一波股价从最高点20元到当前15元的下跌幅度是多少？",
        "下跌幅度为(20-15)/20=25%。",
        images=["missing/price.png"],
    )

    decision = assess_row(row, "candlestick_time_series")

    assert decision.accepted
    assert decision.subtype == "market_price_change_calculation"


def test_long_closing_price_prediction_is_not_high_low_change_calculation():
    row = _row(
        "Predict the stock closing price next month and provide a confidence interval. Historical notes mention the highest point and current decline.",
        "34.80",
    )

    decision = assess_row(row, "candlestick_time_series")

    assert decision.subtype != "market_price_change_calculation"


def test_select_top_deduplicates_content_and_excludes_benchmark_rows():
    candidates = [
        Candidate("text", 1, "a", 10.0, "exact", ("reason",), "task_a", "source_a", 0),
        Candidate("text", 2, "a", 9.0, "exact", ("reason",), "task_b", "source_b", 0),
        Candidate("multi", 3, "b", 8.0, "core", ("reason",), "task_c", "source_c", 1),
        Candidate("multi", 4, "benchmark", 12.0, "exact", ("reason",), "task_d", "source_d", 1),
    ]

    selected = select_top(candidates, count=2, benchmark_hashes={"benchmark"})

    assert [candidate.content_hash for candidate in selected] == ["a", "b"]


def test_select_top_prefers_image_only_when_alignment_scores_are_equal():
    candidates = [
        Candidate("text", 1, "high_text", 10.0, "exact", ("reason",), "task", "source", 0),
        Candidate("multi", 2, "low_image", 9.0, "exact", ("reason",), "task", "source", 1),
        Candidate("text", 3, "tie_text", 8.0, "exact", ("reason",), "task", "source", 0),
        Candidate("multi", 4, "tie_image", 8.0, "exact", ("reason",), "task", "source", 1),
    ]

    selected = select_top(candidates, count=4, benchmark_hashes=set())

    assert [candidate.content_hash for candidate in selected] == [
        "high_text",
        "low_image",
        "tie_image",
        "tie_text",
    ]


def test_select_modality_quota_selects_three_to_one_when_pools_are_sufficient():
    candidates = [
        Candidate("multi", i, f"m{i}", 10.0, "exact", ("reason",), "task", "source", 1)
        for i in range(1, 7)
    ] + [
        Candidate("text", i, f"t{i}", 10.0, "exact", ("reason",), "task", "source", 0)
        for i in range(1, 5)
    ]

    selected = select_modality_quota(
        candidates,
        count=8,
        multimodal_target=6,
        benchmark_hashes=set(),
    )

    assert sum(candidate.image_count > 0 for candidate in selected) == 6
    assert sum(candidate.image_count == 0 for candidate in selected) == 2


def test_select_modality_quota_fills_image_shortfall_with_aligned_text():
    candidates = [
        Candidate("multi", 1, "m1", 10.0, "exact", ("reason",), "task", "source", 1),
        Candidate("text", 2, "t1", 10.0, "exact", ("reason",), "task", "source", 0),
        Candidate("text", 3, "t2", 9.0, "exact", ("reason",), "task", "source", 0),
        Candidate("text", 4, "t3", 8.0, "exact", ("reason",), "task", "source", 0),
    ]

    selected = select_modality_quota(
        candidates,
        count=4,
        multimodal_target=3,
        benchmark_hashes=set(),
    )

    assert [candidate.content_hash for candidate in selected] == ["m1", "t1", "t2", "t3"]


def test_capability_selection_applies_requested_multimodal_target():
    candidates = [
        Candidate("multi", i, f"m{i}", 10.0, "exact", ("reason",), "task", "source", 1)
        for i in range(1, 5)
    ] + [
        Candidate("text", i, f"t{i}", 10.0, "exact", ("reason",), "task", "source", 0)
        for i in range(1, 5)
    ]

    selected = _select_capability(
        "financial_event_extraction",
        candidates,
        count=4,
        multimodal_target=3,
        benchmark_hashes=set(),
    )

    assert sum(candidate.image_count > 0 for candidate in selected) == 3


def test_parse_named_input_preserves_name_and_path():
    name, path = _parse_named_input("rendered=data/rendered.jsonl")

    assert name == "rendered"
    assert str(path).replace("\\", "/") == "data/rendered.jsonl"


def test_content_hash_distinguishes_same_prompt_with_different_images():
    first = _row("<image>请描述图表。", "图表显示收入增长。", images=["a.png"])
    second = _row("<image>请描述图表。", "图表显示收入增长。", images=["b.png"])

    assert _content_hash(first) != _content_hash(second)


def test_entity_disambiguation_accepts_industry_concept_without_other_finance_terms():
    row = _row(
        "你是一个实体消岐助手。请指出以下内容中提及的“户外露营”是不是行业概念。请给出正确选项。\n"
        "近年来，户外露营发展成为休闲娱乐活动，也带动了相关产业发展。\nA. 是\nB. 不是\nC. 不确定",
        "A",
    )

    decision = assess_row(row, "entity_extraction_classification")

    assert decision.accepted
    assert review_alignment(row, "entity_extraction_classification", decision)[0]


def test_fund_comparison_review_accepts_relative_strength_conclusions():
    row = _row(
        "你是一个金融分析师，基金甲和基金乙的择时选股指标如下，请比较两只基金的择时选股能力。\n"
        "|基金|择时能力|选股能力|\n|:--|--:|--:|\n|基金甲|3.9|-0.01|\n|基金乙|10.6|-0.02|",
        "基金乙择时能力更强。两只基金选股能力都较弱，综合绩效均较差。",
    )

    decision = assess_row(row, "portfolio_allocation_risk_return")

    assert decision.accepted
    assert review_alignment(row, "portfolio_allocation_risk_return", decision)[0]


def test_announcement_interpretation_accepts_explicit_positive_impact_request():
    row = _row(
        "你是一个个股研究员。请根据以下公告分析公司收到土地征收补偿款对股价利好体现在哪些方面？\n"
        "公司公告收到土地征收补偿款7400万元。",
        "补偿款增加公司现金流并提升收益水平，对投资者信心和股价可能产生积极影响。",
    )

    decision = assess_row(row, "summary_announcement")

    assert decision.accepted
    assert review_alignment(row, "summary_announcement", decision)[0]


def test_operating_fundamentals_accepts_profitability_table_analysis():
    row = _row(
        "你是一个金融分析师，某公司的主营产品利润如下，请分析公司的经营盈利情况。\n"
        "|产品|营业利润|毛利率|\n|:--|--:|--:|\n|面漆|6380万元|19%|\n|电泳漆|236万元|0.48%|",
        "面漆是主要盈利产品。电泳漆营业利润和毛利率较低，公司盈利能力承压并存在成本控制风险。",
    )

    decision = assess_row(row, "financial_audit_fundamentals")

    assert decision.accepted
    assert review_alignment(row, "financial_audit_fundamentals", decision)[0]


def test_stock_event_interpretation_accepts_strategy_purpose_analysis():
    row = _row(
        "你是一个个股研究员。请根据以下内容分析公司实行股权激励的目的。\n"
        "公司拟向核心技术人员授予限制性股票，并设置未来三年的营业收入考核目标。",
        "股权激励有助于绑定核心人员利益、稳定人才队伍，并推动公司实现收入增长目标。",
    )

    decision = assess_row(row, "summary_announcement")

    assert decision.accepted
    assert review_alignment(row, "summary_announcement", decision)[0]


def test_operating_fundamentals_accepts_generic_accounting_table_conclusion_request():
    row = _row(
        "你是一个金融分析师，以下是某公司的主要会计数据和财务指标，从这些数据中你能得到什么结论？\n"
        "|年度|营业收入|净利润|经营现金流|\n|:--|--:|--:|--:|\n|2022|1000|80|60|\n|2023|1200|70|30|",
        "营业收入有所增长，但净利润和经营现金流下降，说明盈利质量承压且现金回收能力减弱。",
    )

    decision = assess_row(row, "financial_audit_fundamentals")

    assert decision.accepted
    assert review_alignment(row, "financial_audit_fundamentals", decision)[0]


def test_second_stage_review_checks_each_question_answer_pair():
    valid = _row(
        "<image>根据图中RSI走势给出交易建议。",
        "建议等待超卖反转确认后分批买入，并设置止损。",
        images=["missing/rsi.png"],
    )
    invalid = _row(
        "从公告中抽取股票交易事件。",
        '[[0,"Trade",{"shares":"100"}]]',
    )

    accepted = assess_row(valid, "investment_advice_strategy")

    assert review_alignment(valid, "investment_advice_strategy", accepted)[0]
    assert not review_alignment(invalid, "investment_advice_strategy", accepted)[0]


def test_scan_saves_reviewed_candidates_and_cache_can_be_reused(tmp_path):
    source = tmp_path / "train.jsonl"
    source.write_text(
        '{"messages":[{"role":"user","content":"<image>Why did company profit decline?"},'
        '{"role":"assistant","content":"Profit declined because revenue fell and costs increased."}],'
        '"images":["missing/profit.png"],"task":"unrelated_label","split":"test"}\n',
        encoding="utf-8",
    )
    cache = tmp_path / "reviewed_candidates.jsonl"

    scanned = _scan_inputs({"train_text": source}, cache)
    loaded = _load_candidate_cache(cache, {"train_text": source})

    assert scanned == loaded
    assert len(loaded["explanation_anomaly_causality"]) == 1
    assert all(capability in loaded for capability in CAPABILITIES)


def test_incomplete_candidate_cache_is_rejected(tmp_path):
    cache = tmp_path / "reviewed_candidates.jsonl"
    cache.write_text('{"_meta":{"rule_version":"benchmark_alignment_v1"}}\n', encoding="utf-8")

    try:
        _load_candidate_cache(cache, {})
    except ValueError as error:
        assert "cache" in str(error).casefold()
    else:
        raise AssertionError("incomplete cache should not be reused")


def test_long_context_incidental_terms_do_not_trigger_causality_or_candlestick():
    arithmetic = _row(
        "what is the percentage change in cash dividends from 71 to 78? Context: the investment value declined below carrying value due to market prices.",
        "(78 - 71) / 71 = 9.86%",
    )
    correction = _row(
        "挑选有数据错误的描述。问题: 核对公司近三年的总资产。上下文: 另一段材料提到股票成交量和价格走势。",
        "[1, 2, 3]",
    )

    assert not assess_row(arithmetic, "explanation_anomaly_causality").accepted
    assert not assess_row(correction, "candlestick_time_series").accepted


def test_generic_calculation_instruction_does_not_make_risk_analysis_arithmetic():
    row = _row(
        "答案必须由证据支持；涉及计算时保留计算过程。问题: Vendor risk impact on cybersecurity cost structure. 证据材料: 2024年公司有3类风险。",
        "The vendor risk may increase monitoring and incident-response costs.",
    )

    assert not assess_row(row, "basic_arithmetic_metrics").accepted


def test_estimated_chart_value_is_not_multimodal_financial_knowledge():
    row = _row(
        "<image>What is the estimated value of the gaming market in 2017?",
        "The estimated value is 2,216 million dollars, as indicated by the bar chart.",
        images=["missing/market.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_generic_book_title_ocr_is_not_multimodal_financial_knowledge():
    row = _row(
        "<image>What is the title of this book?",
        "Economic Risks of Climate Change: An American Prospectus",
        images=["missing/book.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_ordinary_table_statistics_is_not_multimodal_financial_knowledge():
    row = _row(
        "<image>A farm equipment company recorded tractors made each month. What is the range of the numbers?",
        "The greatest number is 72 and the least is 63, so the range is 9.",
        images=["missing/table.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_generic_company_document_message_is_not_financial_knowledge():
    row = _row(
        "<image>What is the primary message conveyed by the text?",
        "The company teaches consumers how to cook winter squash.",
        images=["missing/document.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_image_chart_ratio_lookup_is_not_multimodal_financial_knowledge():
    row = _row(
        "<image>What is the loan-to-deposit ratio in the global bank industry as of October 2011?",
        "The chart indicates that the global ratio was 74.3%.",
        images=["missing/ratio.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_financial_services_content_usage_is_not_financial_concept_knowledge():
    row = _row(
        "<image>How does IntelligenceBank help financial services clients track product-related content usage?",
        "It provides dashboards, usage reporting, and custom reports.",
        images=["missing/product.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_company_primary_business_remains_multimodal_financial_knowledge():
    row = _row(
        "<image>What does the primary business of the company include?",
        "The company manufactures semiconductors and integrated circuits for customers.",
        images=["missing/report.png"],
    )

    assert assess_row(row, "multimodal_financial_knowledge").accepted


def test_projected_chart_volume_is_not_multimodal_financial_knowledge():
    row = _row(
        "<image>What is the projected volume of the U.S. smart grid market in 2015?",
        "The projected volume is 9.7 billion dollars.",
        images=["missing/grid.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_predicted_increase_chart_value_is_not_financial_knowledge():
    row = _row(
        "<image>What is the predicted increase in online sales by 2018?",
        "The predicted increase is 12.5 percentage points.",
        images=["missing/sales.png"],
    )

    assert not assess_row(row, "multimodal_financial_knowledge").accepted


def test_regulatory_evidence_retrieval_is_not_investment_strategy():
    row = _row(
        "问题: What are the minimum components of an Internal Risk Assessment Process for liquidity risk management? 监管材料: Firms must assess portfolio cash flows.",
        "The framework requires governance, stress testing, limits, and contingency funding plans.",
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_contract_clause_extraction_is_not_compliance_application():
    row = _row(
        "Extract the contract language that answers the legal-review question. Return the relevant clause text only. Contract: The venture must keep GAAP books.",
        "Accurate and complete books of account will be kept in accordance with GAAP.",
        images=["missing/contract.png"],
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_merger_contract_yes_no_modifier_is_not_causal_explanation():
    row = _row(
        "Review the merger-agreement excerpt. Category: Material Adverse Effect. "
        "Question: Failure to meet projections: subject to disproportionate impact modifier. "
        "Contract excerpt: The definition excludes failures to meet projections.",
        "No",
    )

    assert not assess_row(row, "explanation_anomaly_causality").accepted


def test_specific_chart_lookup_is_not_image_caption():
    row = _row(
        "<image>What was the youth unemployment rate in Norway in 2020?",
        "The line chart shows the rate was 9.39% in 2020.",
        images=["missing/chart.png"],
    )

    assert not assess_row(row, "image_caption").accepted


def test_entity_disambiguation_classification_matches_benchmark_operation():
    row = _row(
        '<image>请判断材料中提及的“新动力”是不是股票。新动力(300152.SZ)发布监管公告。A. 是 B. 不是 C. 不确定',
        "A",
        images=["missing/entity.png"],
    )

    decision = assess_row(row, "entity_extraction_classification")

    assert decision.accepted
    assert decision.subtype == "financial_entity_disambiguation"


def test_generic_named_entity_extraction_is_not_entity_disambiguation():
    row = _row(
        "Extract every organization and person mentioned in this article.",
        '{"organizations":["Example Corp"],"persons":["Alice"]}',
    )

    assert not assess_row(row, "entity_extraction_classification").accepted


def test_financial_event_argument_extraction_matches_benchmark_operation():
    row = _row(
        "<image>从金融资讯中抽取以下实体：中标公司、招标方、中标金额、披露日期。",
        '{"argument":"宏润建设","role":"中标公司"} '
        '{"argument":"杭州市地铁集团","role":"招标方"} '
        '{"argument":"132927.19万元","role":"中标金额"}',
        images=["missing/news.png"],
    )

    decision = assess_row(row, "financial_event_extraction")

    assert decision.accepted
    assert decision.subtype == "financial_event_argument_extraction"


def test_financial_event_schema_extraction_is_same_core_operation():
    row = _row(
        "从以下公告中抽取金融事件及其字段: 某上市公司控股股东将400万股质押给某银行。",
        '[[0,"EquityPledge",{"Pledger":"控股股东","PledgedShares":"400万股","Pledgee":"某银行"}]]',
    )

    decision = assess_row(row, "financial_event_extraction")

    assert decision.accepted
    assert decision.subtype == "financial_event_argument_extraction"
    assert review_alignment(row, "financial_event_extraction", decision)[0]


def test_contract_clause_extraction_is_not_financial_event_extraction():
    row = _row(
        "Extract the relevant governing-law clause from this contract.",
        "This agreement is governed by the laws of Delaware.",
    )

    assert not assess_row(row, "financial_event_extraction").accepted


def test_fund_risk_return_comparison_matches_portfolio_benchmark():
    row = _row(
        "<image>请根据两只基金的最高月回报、最低月回报和平均月回报，比较其绩效表现与风险收益特征。",
        "基金A平均回报更高且最低月回报较高，收益表现和下行风险控制均优于基金B。",
        images=["missing/funds.png"],
    )

    decision = assess_row(row, "portfolio_allocation_risk_return")

    assert decision.accepted
    assert decision.subtype == "fund_risk_return_comparison"


def test_nonfinancial_table_comparison_is_not_portfolio_risk_return():
    row = _row(
        "Compare the heights of two buildings in the table.",
        "Building A is taller than Building B.",
    )

    assert not assess_row(row, "portfolio_allocation_risk_return").accepted


def test_financial_leverage_concept_mcq_is_not_fundamentals_analysis():
    row = _row(
        "某公司营业额15亿元、息税前利润3.2亿元。测算财务杠杆系数是为了分析公司的什么？A. 营运能力 B. 财务风险 C. 资产规模 D. 发展能力",
        "财务杠杆系数用于衡量息税前利润变化对每股收益的影响，因此主要用于分析财务风险，答案为B。",
    )

    assert not assess_row(row, "financial_audit_fundamentals").accepted


def test_generic_fund_disclosure_is_not_portfolio_comparison():
    row = _row(
        "基金招募说明书应披露基金的风险收益特征，这体现基金信息披露的哪项作用？A. 风险揭示 B. 价格发现 C. 资产配置",
        "A",
        task="portfolio_allocation_risk_return",
    )

    assert not assess_row(row, "portfolio_allocation_risk_return").accepted


def test_event_extraction_with_price_words_is_not_candlestick():
    row = _row(
        "从下面资讯中抽取金融事件及其字段：某公司公告以10元价格回购股份。",
        '[[{"argument":"某公司","role":"回购方"}]]',
        images=["missing/event.png"],
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_chart_numeric_lookup_is_not_investment_advice():
    row = _row(
        "<image>What is the market forecast value shown for 2026?",
        "The forecast value is 18.5 billion dollars.",
        images=["missing/forecast.png"],
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_market_value_forecast_lookup_is_not_investment_advice():
    row = _row(
        "<image>What is the global avocado oil market value forecast to reach by 2026?",
        "The financial market forecast value is 1.29 billion dollars in 2026.",
        images=["missing/market-value.png"],
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_portfolio_strategy_description_is_not_actionable_investment_advice():
    row = _row(
        "<image>How does the satellite strategy reoptimize its portfolio allocation?",
        "The strategy reoptimizes the portfolio monthly using a quantitative risk-return objective.",
        images=["missing/strategy.png"],
    )

    assert not assess_row(row, "investment_advice_strategy").accepted


def test_image_boll_operation_advice_matches_investment_benchmark():
    row = _row(
        "<image>股价突破BOLL中轨后，投资者应如何操作？",
        "可等待成交量确认后小仓位买入，并把止损设在中轨下方。",
        images=["missing/boll-advice.png"],
    )

    assert assess_row(row, "investment_advice_strategy").accepted


def test_nonformula_numeric_news_task_is_not_basic_arithmetic():
    row = _row(
        "从4条公告中找出导致股价上涨的两条信息，并计算其编号之和。",
        "1和4，编号之和为5。",
    )

    assert not assess_row(row, "basic_arithmetic_metrics").accepted


def test_kpi_summary_with_formula_mentions_is_not_basic_arithmetic():
    row = _row(
        "请总结5家饮料公司应跟踪的KPI，并提取2022年和过去10年的收入、利润率与增长率数据，同时说明这些指标如何计算。",
        "可跟踪收入增长率、毛利率、营业利润率和自由现金流。2022年收入分别为100和120，毛利率=毛利润/收入。",
    )

    assert not assess_row(row, "basic_arithmetic_metrics").accepted


def test_finqa_single_span_lookup_is_not_basic_arithmetic():
    row = _row(
        "### Instruction Calculate or retrieve the requested financial value. ### Question: What was the reported revenue in 2023? Table: 2023 revenue 5,228 million.",
        "分析: 步骤1:Single span 步骤2:5,228 步骤3:N.A. 答案:5,228",
    )

    assert not assess_row(row, "basic_arithmetic_metrics").accepted


def test_stock_price_prediction_is_not_basic_arithmetic():
    row = _row(
        "预测该股票下月收盘价，并按预测结果计算1%的置信区间。历史价格为15.2、15.8和16.1元。",
        "预测收盘价为16.65元，区间为[16.48,16.82]。",
    )

    assert not assess_row(row, "basic_arithmetic_metrics").accepted


def test_gips_image_rule_application_matches_compliance_benchmark():
    row = _row(
        "<image>根据GIPS要求，以下哪项披露符合合规要求？A. 只披露最佳账户 B. 披露完整组合历史 C. 删除亏损年份",
        "B",
        images=["missing/gips.png"],
    )

    assert assess_row(row, "compliance_safety_suitability").accepted


def test_generic_technical_analysis_document_is_not_candlestick_chart_reasoning():
    row = _row(
        "<image>How does technical analysis help in forex trading?",
        "Technical analysis studies historical price movements and indicators to identify possible trends.",
        images=["missing/forex-document.png"],
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_unanswerable_mismatched_kline_question_is_not_candlestick_training():
    row = _row(
        "<image>图中同花顺股票的K线趋势是什么？",
        "无法回答，图中只有诺泰生物的K线图。",
        images=["missing/mismatched-kline.png"],
    )

    assert not assess_row(row, "candlestick_time_series").accepted


def test_buy_rating_reason_is_not_anomaly_causality():
    row = _row(
        "<image>为什么给出买入评级？",
        "因为公司处于行业龙头地位，市场需求复苏，盈利预计上涨。",
        images=["missing/rating.png"],
    )

    assert not assess_row(row, "explanation_anomaly_causality").accepted


def test_entity_disambiguation_is_not_compliance():
    row = _row(
        "<image>判断海天味业是不是公司。A. 股票 B. 公司 C. 行业概念",
        "B",
        images=["missing/entity.png"],
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_financial_report_ranking_is_not_compliance():
    row = _row(
        "你是一位专业的财务分析师，请分析5个公司的财务数据并选择财务状况最好的公司。材料中含有监管处罚信息。",
        "公司C的盈利能力和现金流最好，因此排序为C、B、D、E、A。",
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_contract_clause_classification_is_not_compliance_rule_application():
    row = _row(
        "Classify the contract clause into its legal clause category. Clause: The borrower shall comply with all laws and regulations.",
        "Compliance With Laws",
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_unrelated_stock_news_selection_is_not_compliance():
    row = _row(
        "Please identify content unrelated to the surge of a stock from ten numbered news items, including one regulatory filing.",
        "2, 3, 4, 5",
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_sentiment_prompt_with_regulatory_context_is_not_compliance():
    row = _row(
        "你是一个专业的金融情绪分析助手，请判断用户情绪。背景提到监管政策出台后，投资者对市场前景更加乐观。",
        '["乐观"]',
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_mae_contract_yes_no_is_not_compliance():
    row = _row(
        "Review the merger-agreement excerpt. Category: Material Adverse Effect. Question: MAE Forward looking standard (Y/N). The contract requires compliance with applicable regulations.",
        "Yes",
    )

    assert not assess_row(row, "compliance_safety_suitability").accepted


def test_regulatory_threshold_multiple_choice_matches_compliance():
    row = _row(
        "依据《商业银行资本管理办法》，核心一级资本充足率的最低监管要求是哪项？A. 3% B. 5% C. 8% D. 10%",
        "B",
    )

    assert assess_row(row, "compliance_safety_suitability").accepted


def test_announcement_impact_analysis_matches_summary_benchmark():
    row = _row(
        "<image>请根据公告内容分析公司回购股份对公司经营及股价的影响。",
        "股份回购传递管理层信心并减少流通股份，短期可能稳定股价；用于员工持股计划时还可能改善激励效果。",
        images=["missing/announcement.png"],
    )

    decision = assess_row(row, "summary_announcement")

    assert decision.accepted
    assert decision.subtype == "announcement_business_market_impact"


def test_generic_article_summary_is_not_announcement_impact_analysis():
    row = _row(
        "Summarize the following sports article in one sentence.",
        "The home team won the match in extra time.",
    )

    assert not assess_row(row, "summary_announcement").accepted


def test_audit_opinion_analysis_matches_financial_audit_benchmark():
    row = _row(
        "<image>审计机构因无法取得充分适当的证据而出具保留意见，请分析原因及需要关注的财务风险。",
        "保留意见源于应收款可收回性和坏账准备缺乏充分审计证据，需关注资金占用、减值计提及资产质量风险。",
        images=["missing/audit.png"],
    )

    decision = assess_row(row, "financial_audit_fundamentals")

    assert decision.accepted
    assert decision.subtype == "audit_opinion_risk_analysis"


def test_business_segment_operating_analysis_matches_audit_fundamentals():
    row = _row(
        "<image>根据主营项目的营业收入、营业成本、营业利润和毛利率，分析公司的经营情况。",
        "主营业务贡献了大部分收入和利润，毛利率保持稳定；其他业务规模较小，成本控制仍有改善空间。",
        images=["missing/segments.png"],
    )

    decision = assess_row(row, "financial_audit_fundamentals")

    assert decision.accepted
    assert decision.subtype == "operating_fundamentals_analysis"


def test_audit_clause_retrieval_is_not_financial_audit_analysis():
    row = _row(
        "Return the exact sentence that states the auditor's responsibility.",
        "The auditor is responsible for obtaining reasonable assurance.",
    )

    assert not assess_row(row, "financial_audit_fundamentals").accepted
