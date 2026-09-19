# Scoring Methodology Specification (Version 1.0)

## 1. Transparency Principle

The scoring system avoids arbitrary, unexplained "black-box" scores. All calculations are:
- Strictly reproducible.
- Expressed in clear mathematical fractions.
- Accompanied by full formula metadata in the final report.

---

## 2. Component Rates

### Mention Rate ($R_{\text{mention}}$)
Measures the frequency of the target brand's appearance across valid model responses:
$$R_{\text{mention}} = \frac{N_{\text{responses with brand}}}{N_{\text{successful responses}}}$$

### Recommendation Rate ($R_{\text{rec}}$)
Measures the frequency with which the brand is affirmatively endorsed or included as a recommended solution:
$$R_{\text{rec}} = \frac{N_{\text{responses with RECOMMENDED or STRONGLY\_RECOMMENDED}}}{N_{\text{successful responses}}}$$

### Topic Coverage ($C_{\text{topic}}$)
Measures the breadth of category visibility:
$$C_{\text{topic}} = \frac{N_{\text{topics with } \ge 1 \text{ brand mention}}}{N_{\text{total topics audited}}}$$

### Competitor Parity Factor ($P_{\text{comp}}$)
Evaluates whether the brand maintains presence in spaces where competitors are active:
$$P_{\text{comp}} = \min\left(1.0, \frac{R_{\text{mention}}}{\max(0.01, R_{\text{competitor}})}\right)$$
*(If competitor presence rate is 0, $P_{\text{comp}} = 1.0$.)*

---

## 3. Composite Visibility Score (0 to 100)

The composite score summarizes overall model visibility across a balanced weighted distribution:

| Component Metric | Weight | Maximum Points | Strategic Rationale |
| :--- | :---: | :---: | :--- |
| **Mention Rate** | 35% | 35.0 pts | Foundational brand presence across prompt answers |
| **Recommendation Rate** | 30% | 30.0 pts | Qualitative positioning as an advocated solution |
| **Topic Coverage** | 20% | 20.0 pts | Breadth of relevance across industry topics |
| **Competitor Parity** | 15% | 15.0 pts | Resilience against competitor exclusivity |
| **Total** | **100%** | **100.0 pts** | **Deterministic Composite Score** |

$$\text{Composite Score} = (R_{\text{mention}} \times 35) + (R_{\text{rec}} \times 30) + (C_{\text{topic}} \times 20) + (P_{\text{comp}} \times 15)$$

---

## 4. Visibility Gap Classification

| Gap Type | Severity | Trigger Condition |
| :--- | :---: | :--- |
| **COMPETITOR_PRESENCE_GAP** | `CRITICAL` | Brand is absent while a competitor appears in the answer. |
| **TOPIC_INVISIBILITY_GAP** | `HIGH` | Brand receives 0 mentions across an entire topic cluster ($\ge 2$ prompts). |
| **WEAK_RECOMMENDATION_GAP** | `MEDIUM` | Brand is mentioned but framed incidentally without endorsement. |
| **PROVIDER_DISCREPANCY_GAP** | `LOW` | Brand appears in one provider (e.g. OpenAI) but is omitted by another (e.g. Gemini) on the identical prompt. |
