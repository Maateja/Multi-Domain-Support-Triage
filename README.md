# AI Support Triage Agent

This is a terminal-based, offline AI Support Triage Agent built in Python. It processes customer support tickets from a CSV file across three platforms: **HackerRank, Claude, and Visa**.

The system relies strictly on keyword-based NLP heuristics and deterministic logic. It does **not** rely on external APIs, hallucinations, or external knowledge bases, ensuring 100% policy compliance, data safety, and repeatable output.

---

## 🎯 Features & Pipeline Architecture

The agent processes each ticket through a rigorous pipeline to understand its intent, assess financial/security risk, and formulate a safe response or escalation:

1. **Input Preprocessing**: Cleans input text and normalizes spaces for accurate keyword mapping.
2. **Request Classification**: Categorizes the ticket into one of four types:
   - `product_issue`
   - `feature_request`
   - `bug`
   - `invalid`
3. **Product Area Mapping**: Contextually maps the ticket to predefined domains (`account`, `billing`, `payments`, `assessments`, `api_usage`, or `fraud_security`).
4. **Advanced Risk Detection**: Scans the text for high-risk flags indicating financial anomalies or security breaches (e.g., *"fraud"*, *"stolen"*, *"breach"*, *"refund"*, *"chargeback"*).
5. **Decision & Escalation Logic**: 
    - Immediately escalates high-risk cases, critical bugs, prompt injections, and feature requests to specialized human teams.
    - Standard queries are marked as `replied`.
6. **Tone-Matched Response Generation**: Generates safe, generic, company-specific responses based on the product area. (e.g., distinguishing between HackerRank hiring queries, Claude API limits, and Visa payment disputes).
7. **CSV Output**: Safely strips out newlines (`\n`) and writes exactly the 5 required columns (`status`, `product_area`, `response`, `justification`, `request_type`) ensuring maximum compatibility with Excel and CSV parsers.

---

## 📁 File Structure

- `triage_agent.py`: The main CLI application containing the core logic and pipeline.
- `files/asset/upload/support_tickets.csv`: The default input CSV file containing the raw support tickets.
- `output.csv`: The generated output file containing the processed and classified tickets.

---

## 🚀 Usage Instructions

The script is entirely self-contained. It reads from the standard input CSV and writes directly to `output.csv`.

### Run the Agent
Execute the following command in your terminal:
```bash
python triage_agent.py
```

### Custom File Paths
If you need to specify different input or output paths, you can pass them as arguments:
```bash
python triage_agent.py --input path/to/input.csv --output path/to/custom_output.csv
```

> **Note on CSV Files**: Ensure that `output.csv` is **not open in Excel** while running the script, as Windows locks open files, which will cause a `Permission denied` error.

---

## 🛡️ Edge Cases Handled Successfully

- **Prompt Injection Prevention**: Tickets asking to *"ignore previous prompts"* or *"delete code"* are classified as `invalid` and escalated immediately.
- **Dynamic Bug Handling**: General technical difficulties are replied to safely with troubleshooting steps, whereas *"critical"* outages or complete platform crashes are automatically escalated.
- **Excel Compatibility**: All internal newlines and carriage returns within responses and justifications are sanitized into spaces, ensuring columns do not break when viewed in spreadsheet software.
