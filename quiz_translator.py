import os, sys, json, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data", "quiz_thai_cache.json")
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

_cache = {}
_norm_cache = {}

def load_cache():
    global _cache, _norm_cache
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                _cache = json.load(f)
                _norm_cache = {re.sub(r'[^a-zA-Z0-9]+', '', k.lower()): v for k, v in _cache.items() if k}
        except Exception:
            _cache = {}
            _norm_cache = {}

load_cache()

def clean_thai_spacing(text):
    if not text:
        return ""
    # Remove HTML entities like &quot; if any
    text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    
    # Clean jammed English labels from extraction
    text = re.sub(r'Exam traps?\s*', 'Exam Trap: ', text)
    text = re.sub(r'Predict first\s*', 'Predict First: ', text)
    text = re.sub(r'On the exam\s*', 'On the Exam: ', text)
    text = re.sub(r'Why is that wrong\?\s*', ' (ทำไมถึงผิด): ', text)
    
    # Proper spacing between Thai and English/Digits
    text = re.sub(r'([\u0e00-\u0e7f])([A-Za-z0-9])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z0-9])([\u0e00-\u0e7f])', r'\1 \2', text)
    
    # Parentheses spacing
    text = re.sub(r'([\u0e00-\u0e7f])\(', r'\1 (', text)
    text = re.sub(r'\)([\u0e00-\u0e7f])', r') \1', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    
    # Punctuation spacing (no space before colon, comma, period, question mark)
    text = re.sub(r'\s+([,.:;?!])', r'\1', text)
    
    # Collapse multiple whitespaces
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def trans_one(text):
    if not text:
        return ""
    text_clean = text.strip()
    if text_clean in _cache:
        return _cache[text_clean]
    
    norm_k = re.sub(r'[^a-zA-Z0-9]+', '', text_clean.lower())
    if norm_k in _norm_cache:
        return _norm_cache[norm_k]
    
    # If text is already predominantly Thai
    thai_chars = len(re.findall(r'[\u0e00-\u0e7f]', text_clean))
    if thai_chars > len(text_clean) * 0.4:
        res = clean_thai_spacing(text_clean)
        _cache[text_clean] = res
        _norm_cache[norm_k] = res
        return res

    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=th&dt=t&q=' + urllib.parse.quote(text_clean)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode())
            translated = ''.join([part[0] for part in data[0] if part[0]])
            cleaned = clean_thai_spacing(translated)
            _cache[text_clean] = cleaned
            _norm_cache[norm_k] = cleaned
            return cleaned
    except Exception:
        pass
            
    # Fallback if network fails or times out
    fallback = clean_thai_spacing(text_clean)
    _cache[text_clean] = fallback
    _norm_cache[norm_k] = fallback
    return fallback

def save_cache():
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving cache:", e)

def get_thai_explanation(text):
    if not text: return ""
    return trans_one(text)

if __name__ == "__main__":
    print(f"Loaded {len(_cache)} cached translations, {len(_norm_cache)} normalized entries.")
