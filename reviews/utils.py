BANNED_WORDS = [
    'spam', 'fake', 'scam', 'fraud',
    # أضف كلمات عربية لو تبي
]

def check_for_banned_words(text):
    """
    يتحقق إذا النص فيه كلمات ممنوعة
    يرجع (is_flagged, reason)
    """
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True, f"Contains banned word: '{word}'"
    return False, ""