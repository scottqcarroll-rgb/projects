#!/usr/bin/env python3
"""
LLM-powered email classifier using local Gemma 4 via HTTP.
Falls back to rule-based keywords if LLM is unavailable.
"""

import json
import requests
import sys

LLM_URL = "http://192.168.1.174:8081/v1/completions"
LLM_MODEL = "gemma-4-E4B-it"

FALLBACK_KEYWORDS = {
    'important': [
        'urgent', 'asap', 'action required', 'confirm', 'approval', 'signature',
        'respond', 'reply needed', 'critical', 'important',
        'deadline', 'due', 'expires', 'today', 'tomorrow', 'meeting',
        'invoice', 'payment', 'contract', 'agreement', 'legal', 'purchase',
        'billing', 'refund', 'expense',
        'project', 'task', 'assigned', 'review', 'feedback', 'performance',
        'hiring', 'job', 'interview', 'offer', 'salary',
    ],
    'not_important': [
        'newsletter', 'promotional', 'promotion', 'sale', 'discount', 'offer',
        'unsubscribe', 'marketing', 'coupon', 'deal', 'limited time',
        'liked your post', 'commented', 'followed you', 'new follower',
        'automated', 'auto-generated', 'do not reply', 'no-reply',
        'notification', 'digest', 'weekly summary', 'monthly digest',
        'welcome to', 'thanks for signing up', 'verify your email',
        'confirm subscription',
    ]
}

def llm_classify_batch(emails_data):
    """Classify a batch of emails using the local LLM."""
    if not emails_data:
        return []
    
    # Build prompt
    emails_text = ""
    for i, e in enumerate(emails_data):
        sender = e.get('from', e.get('sender', 'Unknown'))
        subject = e.get('subject', 'No subject')
        snippet = e.get('snippet', '')[:200]
        body_text = e.get('body', snippet)[:500]
        emails_text += f"\n--- Email {i+1} ---\n"
        emails_text += f"From: {sender}\n"
        emails_text += f"Subject: {subject}\n"
        emails_text += f"Snippet: {snippet}\n"
        emails_text += f"Body preview: {body_text}\n"
    
    prompt = f"""You are an email classifier. For each email below, output exactly 3 lines:
<important_N>YES or NO</important_N>
<reason_N>one sentence reason</reason_N>
<action_N>specific action or none</action_N>

Example:
<important_1>YES</important_1>
<reason_1>From boss, requires confirmation of deadline</reason_1>
<action_1>Reply to confirm availability</action_1>
<important_2>NO</important_2>
<reason_2>Promotional newsletter with sale</reason_2>
<action_2>none</action_2>

Now classify these {len(emails_data)} emails:
{emails_text}"""

    try:
        response = requests.post(
            LLM_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "max_tokens": 800,
                "temperature": 0.1
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        # Try different response formats
        text = ""
        if 'choices' in result and len(result['choices']) > 0:
            choice = result['choices'][0]
            text = choice.get('text', choice.get('message', {}).get('content', ''))
        elif 'content' in result:
            text = result['content'][0].get('text', '')
        elif 'response' in result:
            text = result['response']
        
        if not text:
            return fallback_classify(emails_data)
        
        # Parse LLM response
        classifications = []
        lines = text.strip().split('\n')
        
        current_important = None
        current_reason = None
        current_action = None
        email_idx = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for tagged format: <important_N>YES</important_N>
            if '<important_' in line and '</important_' in line:
                start = line.find('>') + 1
                end = line.rfind('<')
                val = line[start:end].strip()
                current_important = val == 'YES'
            elif '<reason_' in line and '</reason_' in line:
                start = line.find('>') + 1
                end = line.rfind('<')
                current_reason = line[start:end].strip()
            elif '<action_' in line and '</action_' in line:
                start = line.find('>') + 1
                end = line.rfind('<')
                current_action = line[start:end].strip()
                
                # We have all three fields - emit classification
                if current_important is not None and current_reason and current_action:
                    classifications.append({
                        'important': current_important,
                        'reason': current_reason,
                        'action': current_action
                    })
                    email_idx += 1
                    current_important = None
                    current_reason = None
                    current_action = None
        
        # Parse by numbered pattern if tagged format didn't work
        if not classifications:
            import re as _re
            for i in range(len(emails_data)):
                # Look for "Email N" or just numbered entries
                patterns = [
                    rf'Email {i+1}[:\s]+(IMPORTANT|NOT.?IMPORTANT)[^\n]*\n([^\n]+)',
                    rf'{i+1}[.):\s]+(IMPORTANT|NOT.?IMPORTANT)',
                    rf'\[{i+1}\][\s:]*(IMPORTANT|NOT.?IMPORTANT)',
                ]
                matched = False
                for pattern in patterns:
                    m = _re.search(pattern, text, _re.IGNORECASE)
                    if m:
                        imp = m.group(1).upper().startswith('IMP')
                        classifications.append({
                            'important': imp,
                            'reason': m.group(2).strip() if m.lastindex >= 2 else '',
                            'action': 'none'
                        })
                        matched = True
                        break
                if not matched:
                    classifications.append({
                        'important': False, 'reason': '', 'action': 'none'
                    })
        
        # Ensure we have exactly len(emails_data) classifications
        while len(classifications) < len(emails_data):
            # Try to parse from text in a simpler way
            classifications.append({'important': False, 'reason': '', 'action': 'none'})
        classifications = classifications[:len(emails_data)]
        
        return classifications
        
    except Exception as e:
        print(f"[LLM CLASSIFY] LLM unavailable ({e}), using fallback", file=sys.stderr)
        return fallback_classify(emails_data)


def fallback_classify(emails_data):
    """Rule-based fallback classification."""
    import re as _re
    results = []
    for e in emails_data:
        text = f"{e.get('from', '')} {e.get('subject', '')} {e.get('body', e.get('snippet', ''))}".lower()
        
        important_score = sum(1 for kw in FALLBACK_KEYWORDS['important'] if kw in text)
        not_important_score = sum(1 for kw in FALLBACK_KEYWORDS['not_important'] if kw in text)
        
        is_important = important_score > not_important_score
        
        reason = "Matched important keywords" if is_important else "Matched promotional/automated keywords"
        action = "Review" if is_important else "none"
        
        if '@' in e.get('from', ''):
            sender_domain = e['from'].split('@')[-1].replace('>', '').strip()
            if sender_domain in ['company.com', 'work']:
                is_important = True
                reason = "Known work domain"
        
        results.append({
            'important': is_important,
            'reason': reason,
            'action': action
        })
    return results


def classify_emails(emails):
    """Main classify function - tries LLM, falls back to keywords."""
    # Prepare data for LLM
    emails_data = []
    for e in emails:
        emails_data.append({
            'from': e.get('sender', e.get('from', 'Unknown')),
            'subject': e.get('subject', 'No subject'),
            'snippet': e.get('snippet', ''),
            'body': e.get('body', e.get('snippet', ''))
        })
    
    return llm_classify_batch(emails_data)
