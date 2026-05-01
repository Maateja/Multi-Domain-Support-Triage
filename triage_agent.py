import csv
import re
import sys
import argparse

class TriageAgent:
    """
    Main triage agent that processes tickets from a CSV file.
    """
    def __init__(self):
        self.risk_keywords = {
            "fraud", "unauthorized", "stolen", "hacked", "compromised", 
            "breach", "scam", "phishing", "leak", "threat", "police", "vulnerability",
            "refund", "chargeback", "dispute"
        }
        
        self.product_area_keywords = {
            "account": ["login", "password", "email", "2fa", "profile", "account", "locked", "access", "reset", "identity", "seat", "owner", "admin", "remove"],
            "billing": ["charge", "invoice", "refund", "billing", "subscription", "fee", "cost", "paid", "money"],
            "payments": ["payment", "transaction", "transfer", "card", "debit", "credit", "declined", "merchant"],
            "assessments": ["test", "interview", "assessment", "score", "hackerrank", "compiler", "submit", "challenge", "candidate", "interviewer"],
            "api_usage": ["api", "token", "rate limit", "endpoint", "integration", "rest", "webhook", "429"],
            "fraud_security": ["fraud", "hacked", "unauthorized", "security", "stolen", "breach", "vulnerability"],
        }
        
        self.type_keywords = {
            "feature_request": ["add", "feature", "wish", "new", "support for", "would be nice", "propose", "suggest"],
            "bug": ["error", "bug", "broken", "crashing", "not working", "fails", "issue", "crash", "exception", "glitch", "wrong", "429", "down", "failing"],
            "product_issue": ["how to", "cannot find", "where is", "help with", "question", "explain", "guide", "help", "update", "change"]
        }
        
    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def detect_risk(self, text_lower):
        words = re.findall(r'\b\w+\b', text_lower)
        return any(rk in words for rk in self.risk_keywords)

    def classify_product_area(self, text_lower, default="general"):
        words = re.findall(r'\b\w+\b', text_lower)
        scores = {area: 0 for area in self.product_area_keywords}
        for area, keywords in self.product_area_keywords.items():
            for kw in keywords:
                if kw in words or kw in text_lower:
                    scores[area] += 1
        
        best_area = max(scores, key=scores.get)
        if scores[best_area] == 0:
            return default
        return best_area

    def classify_request_type(self, text_lower):
        words = re.findall(r'\b\w+\b', text_lower)
        if len(words) < 3 or set(words).issubset({"test", "asdf", "hello"}) or len(set(words)) < 2:
            return "invalid"
            
        scores = {req_type: 0 for req_type in self.type_keywords}
        for req_type, keywords in self.type_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[req_type] += 1
                    
        best_type = max(scores, key=scores.get)
        if scores[best_type] == 0:
            return "product_issue"
        return best_type
        
    def generate_safe_response(self, product_area, company, text_lower):
        company_str = company if company and company.lower() != "none" else "our platform"
        company_lower = company.lower() if company else ""
        
        if company_lower == "hackerrank":
            if "hiring" in text_lower or "infosec" in text_lower:
                return "To use HackerRank for hiring or set up compliance requirements, please contact the sales or onboarding team to complete setup."
            elif product_area == "assessments":
                return "Hi,\n\nTest policies, including time limits and scores, are set by the administering company. Please ensure you are using a supported browser and a stable internet connection. If you are experiencing technical difficulties, clear your browser cache or switch to an incognito window."
            elif product_area == "account":
                return "To update or recover your HackerRank account, please navigate to your Profile Settings. For security reasons, we cannot manually override account settings or permissions."
            else:
                return "Hi,\n\nThank you for reaching out. Please refer to the HackerRank Support Center for step-by-step guides on managing your tests and subscriptions."
                
        elif company_lower == "claude":
            if product_area == "account":
                return "To regain access or modify workspace seats, please contact your workspace admin. For security reasons, Claude Support cannot manually modify account access or ownership."
            elif product_area == "api_usage":
                return "Claude API rate limits depend on your tier. If you are receiving 429 errors, please check your console dashboard to verify your limits and billing status."
            else:
                return "Thank you for contacting Claude support. For data privacy and terms of use, please review our official trust and safety documentation."
                
        elif company_lower == "visa":
            if product_area == "payments" or product_area == "billing" or product_area == "fraud_security":
                return "Call the issuer immediately. If you have a specific dispute, please follow the formal dispute process in the app or website. Refunds can typically be arranged within standard business hours subject to T&Cs."
            else:
                return "Please contact Visa Support using the number on the back of your card for assistance with your account. We take your security seriously."
                
        # Generic fallback
        if product_area == "account":
            return f"Thank you for contacting support. For account access or changes, please refer to your settings. We cannot manually modify account access for security reasons."
        elif product_area == "billing" or product_area == "payments":
            return f"For billing or refunds, please review your dashboard. If you have a specific dispute, please follow the formal dispute process."
        else:
            return f"Thank you for reaching out. We recommend checking our official documentation for the most accurate guidance on this topic."

    def process_ticket(self, issue, subject, company):
        issue_cl = self.clean_text(issue)
        subject_cl = self.clean_text(subject)
        
        full_text = f"{subject_cl} {issue_cl}".lower()
        
        req_type = self.classify_request_type(full_text)
        product_area = self.classify_product_area(full_text)
        is_high_risk = self.detect_risk(full_text)
        
        # Override for explicit payment disputes or high risk Visa cases
        if (company == "Visa" and ("stolen" in full_text or "unauthorized" in full_text)) or is_high_risk:
            product_area = "fraud_security"
            
        status = "replied"
        response = ""
        
        # Determine status and initial response mapping
        if is_high_risk:
            status = "escalated"
            response = "Your issue has been escalated to our specialized human support team for immediate review."
        elif req_type == "invalid":
            status = "escalated"
            response = "I am sorry, this is out of scope from my capabilities."
        elif req_type == "feature_request":
            status = "escalated"
            response = "Thank you for your feature request. We have escalated this to our product team."
        elif req_type == "bug":
            if "critical" in full_text or "down" in full_text:
                status = "escalated"
                response = "We detected a critical outage or bug. This issue has been immediately escalated to our engineering team."
            else:
                status = "replied"
                response = self.generate_safe_response(product_area, company, full_text)
        else:
            # Multi-intent handling: if there are multiple parts of the issue, we could mark as higher complexity
            if " and " in full_text and len(full_text.split(" and ")) > 2:
                # Mild complexity markup - but we still reply if safe
                pass
            status = "replied"
            response = self.generate_safe_response(product_area, company, full_text)

        # Security/Prompt Injection checks overrule others
        if "ignore" in full_text and "prompt" in full_text or "code" in full_text and "delete" in full_text:
            status = "escalated"
            product_area = "fraud_security"
            response = "I am sorry, this is out of scope from my capabilities."

        justification = f"{req_type} detected, mapped to {product_area}, risk={'high' if is_high_risk else 'low'}"
        
        return {
            "status": status.lower(),
            "product_area": product_area.lower(),
            "response": response,
            "justification": justification,
            "request_type": req_type.lower()
        }

def process_csv(input_file, output_file):
    agent = TriageAgent()
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            rows = list(reader)
    except Exception as e:
        print(f"Error reading {input_file}: {e}", file=sys.stderr)
        sys.exit(1)
        
    out_rows = []
    
    for row in rows:
        issue = row.get('Issue', '')
        subject = row.get('Subject', '')
        company = row.get('Company', 'None')
        
        result = agent.process_ticket(issue, subject, company)
        
        # Only exactly these 5 columns
        out_row = {
            'status': result['status'],
            'product_area': result['product_area'],
            'response': result['response'].replace('\n', ' ').replace('\r', '').strip(),
            'justification': result['justification'].replace('\n', ' ').replace('\r', '').strip(),
            'request_type': result['request_type']
        }
        out_rows.append(out_row)
        
    fieldnames = ['status', 'product_area', 'response', 'justification', 'request_type']
    
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Successfully processed {len(rows)} tickets and saved to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Support Triage Agent CSV Processor")
    parser.add_argument("--input", type=str, default="files/asset/upload/support_tickets.csv", help="Input CSV file")
    parser.add_argument("--output", type=str, default="output.csv", help="Output CSV file")
    
    args = parser.parse_args()
    process_csv(args.input, args.output)
