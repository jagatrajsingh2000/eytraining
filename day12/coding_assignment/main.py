import os
import faiss
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize
load_dotenv()
FAQS = [
    "Q: How do I reset my password? A: Click Forgot Password on the login page and follow the email link.",
    "Q: How can I track my order? A: Open Orders, select your order, and check the tracking status.",
    "Q: What is the refund policy? A: Refunds are available within 30 days for eligible unused products.",
    "Q: How do I contact support? A: Use the Help page chat form or email support@example.com.",
    "Q: Can I change my delivery address? A: You can edit the address before the order is shipped.",
    "Q: How do I cancel an order? A: Open Orders and select Cancel if the order has not shipped.",
    "Q: Which payment methods are supported? A: Cards, UPI, net banking, and supported wallets are accepted.",
    "Q: How do I update my profile? A: Go to Account Settings and edit your personal information.",
    "Q: Why was my payment declined? A: Check card details, bank limits, or try another payment method.",
    "Q: How can I return my order? A: Open Orders, choose the item, and start a return request.",
]

vectorizer = HashingVectorizer(n_features=384, alternate_sign=False, norm=None)
faq_vectors = normalize(vectorizer.transform(FAQS), norm="l2").astype(np.float32).toarray()
index = faiss.IndexFlatIP(faq_vectors.shape[1])
index.add(faq_vectors)

def retrieve(query, top_k=2):
    query_vector = normalize(vectorizer.transform([query]), norm="l2").astype(np.float32).toarray()
    scores, indexes = index.search(query_vector, top_k)
    return [(FAQS[i], float(score)) for i, score in zip(indexes[0], scores[0])]

def generate_answer(query, matches):
    context = "\n".join(f"- {faq} (score={score:.3f})" for faq, score in matches)
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return f"Offline answer:\n{matches[0][0]}\n\nRetrieved:\n{context}"
    client = Groq(api_key=key)
    try:
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {"role": "system", "content": "Answer concisely using only the retrieved FAQs."},
                {"role": "user", "content": f"User query: {query}\nRetrieved FAQs:\n{context}"},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"Groq unavailable ({exc}). Offline answer:\n{matches[0][0]}\n\nRetrieved:\n{context}"


print("Smart FAQ Bot. Type 'exit' to quit.")
while True:
    user_query = input("\nYou: ").strip()
    if user_query.lower() == "exit":
        break
    results = retrieve(user_query)
    print("\nBot:", generate_answer(user_query, results))
    print("Top scores:", ", ".join(f"{score:.3f}" for _, score in results))

