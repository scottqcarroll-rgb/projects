import json

# Rule-based email importance classifier (no API required - completely free)

IMPORTANT_KEYWORDS = [
    # Action words
    'urgent', 'asap', 'action required', 'confirm', 'approval', 'signature',
    'respond', 'reply needed', 'update', 'critical', 'important',

    # Time-sensitive
    'deadline', 'due', 'expires', 'ends', 'deadline', 'today', 'tomorrow',
    'meeting', 'appointment', 'call at', 'scheduled',

    # Financial/Legal
    'invoice', 'payment', 'receipt', 'contract', 'agreement', 'legal',
    'purchase', 'billing', 'refund', 'expense', 'report',

    # Personal/Work
    'project', 'task', 'assigned', 'review', 'feedback', 'performance',
    'hiring', 'job', 'interview', 'offer', 'salary',
]

NOT_IMPORTANT_KEYWORDS = [
    # Marketing/Promotional
    'newsletter', 'promotional', 'promotion', 'sale', 'discount', 'offer',
    'unsubscribe', 'marketing', 'coupon', 'deal', 'limited time',
    '50% off', '% off', 'free shipping', 'special offer',

    # Social media
    'liked your post', 'commented', 'followed you', 'new follower',
    'social media', 'instagram', 'facebook', 'twitter', 'linkedin',

    # Automated/Low priority
    'automated', 'auto-generated', 'do not reply', 'no-reply',
    'notification', 'digest', 'weekly summary', 'monthly digest',

    # Low value
    'welcome to', 'thanks for signing up', 'verify your email',
    'confirm subscription', 'welcome aboard',
]

IMPORTANT_SENDERS = [
    '@company.com', '@work', '@corporate',  # Work domains
    'boss', 'manager', 'executive', 'director', 'ceo',
    'hr@', 'finance@', 'legal@', 'compliance@',
]

NOT_IMPORTANT_SENDERS = [
    'newsletter', 'marketing', 'promo', 'deals', 'sale',
    'noreply', 'no-reply', 'automated', 'notification',
    'social', 'instagram', 'facebook', 'twitter', 'tiktok',
]


def classify_emails(emails):
    """Classify emails using rule-based keywords (completely free, no API)."""
    if not emails:
        return []

    classifications = []

    for email in emails:
        subject = (email.get('subject', '') or '').lower()
        sender = (email.get('from', '') or '').lower()
        snippet = (email.get('snippet', '') or '').lower()
        combined = f"{subject} {sender} {snippet}".lower()

        # Calculate importance score
        importance_score = _calculate_score(
            subject, sender, snippet, combined
        )

        # Determine importance level
        if importance_score > 0:
            importance = 'important'
            reason = _get_reason(subject, sender, snippet, combined, True)
        else:
            importance = 'not_important'
            reason = _get_reason(subject, sender, snippet, combined, False)

        classifications.append({
            'id': email['id'],
            'importance': importance,
            'reason': reason
        })

    return classifications


def _calculate_score(subject, sender, snippet, combined):
    """Calculate importance score based on keywords."""
    score = 0

    # Check important keywords
    for keyword in IMPORTANT_KEYWORDS:
        if keyword in combined:
            score += 2

    # Check not important keywords
    for keyword in NOT_IMPORTANT_KEYWORDS:
        if keyword in combined:
            score -= 3

    # Check sender patterns
    for pattern in IMPORTANT_SENDERS:
        if pattern in sender:
            score += 2

    for pattern in NOT_IMPORTANT_SENDERS:
        if pattern in sender:
            score -= 2

    # Boost for personal-looking addresses (not marketing)
    if '@' in sender and not any(x in sender for x in ['noreply', 'no-reply', 'newsletter', 'marketing']):
        if not any(x in sender for x in ['company', 'brands', 'deals']):
            score += 1

    # Penalize if clearly marketing
    if 'unsubscribe' in snippet:
        score -= 2

    return score


def _get_reason(subject, sender, snippet, combined, is_important):
    """Generate a reason for the classification."""
    if is_important:
        # Find which keyword triggered importance
        for keyword in IMPORTANT_KEYWORDS:
            if keyword in combined:
                if keyword in ['urgent', 'asap', 'critical']:
                    return "Marked as urgent or critical."
                elif keyword in ['deadline', 'due', 'expires']:
                    return "Contains time-sensitive deadline."
                elif keyword in ['meeting', 'appointment', 'call at']:
                    return "Meeting or appointment scheduled."
                elif keyword in ['invoice', 'payment', 'receipt']:
                    return "Financial or billing-related."
                elif keyword in ['action required', 'confirm', 'approval']:
                    return "Requires your action or approval."
                elif keyword in ['project', 'task', 'assigned']:
                    return "Work project or task assignment."

        # Check sender
        for pattern in IMPORTANT_SENDERS:
            if pattern in sender:
                return "From an important contact or department."

        return "Contains important keywords."
    else:
        # Find which keyword triggered not important
        for keyword in NOT_IMPORTANT_KEYWORDS:
            if keyword in combined:
                if keyword in ['newsletter', 'digest', 'summary']:
                    return "Newsletter or digest email."
                elif keyword in ['promotional', 'sale', 'discount', 'offer']:
                    return "Promotional or marketing email."
                elif keyword in ['liked', 'commented', 'followed', 'social']:
                    return "Social media notification."
                elif keyword in ['unsubscribe', 'no-reply', 'automated']:
                    return "Automated notification email."

        # Check sender
        for pattern in NOT_IMPORTANT_SENDERS:
            if pattern in sender:
                return "From marketing or notification system."

        return "Low priority based on content."


if __name__ == '__main__':
    test_emails = [
        {
            "id": "msg1",
            "from": "boss@company.com",
            "subject": "Project deadline moved to Friday - URGENT",
            "snippet": "The client requested we move the deadline...",
            "date": "2024-01-15"
        },
        {
            "id": "msg2",
            "from": "newsletter@retailer.com",
            "subject": "50% off everything this weekend!",
            "snippet": "Limited time offer from your favorite retailer. Unsubscribe here...",
            "date": "2024-01-15"
        },
        {
            "id": "msg3",
            "from": "hr@company.com",
            "subject": "Please confirm your meeting tomorrow at 2pm",
            "snippet": "Hi, we have a meeting scheduled for tomorrow...",
            "date": "2024-01-15"
        }
    ]

    try:
        results = classify_emails(test_emails)
        print("[OK] Classifications (rule-based, free):")
        for r in results:
            print(f"  {r['id']}: {r['importance']} - {r['reason']}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
