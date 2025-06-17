def clean_numeric_string(value_str):
    if not value_str:
        return None
    cleaned = str(value_str).replace(',', '').replace(' ', '')
    if cleaned.endswith('.'):
        cleaned = cleaned[:-1]
    if cleaned.count('.') > 1:
        first_dot = cleaned.find('.')
        cleaned = cleaned[:first_dot+1] + cleaned[first_dot+1:].replace('.', '')
    return cleaned