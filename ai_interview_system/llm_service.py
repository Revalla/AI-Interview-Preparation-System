import os
import json
from dotenv import load_dotenv
import openai
import random

# Mock question bank for fallback when API is unavailable
MOCK_QUESTIONS = {
    "AI/ML Engineer": {
        "Easy": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain what a neural network is in simple terms.",
            "What is overfitting and how do you prevent it?",
            "Describe the role of activation functions in neural networks.",
            "What is the purpose of batch normalization?"
        ],
        "Medium": [
            "How does gradient descent work and what are its limitations?",
            "Explain the bias-variance tradeoff in machine learning.",
            "What is transfer learning and when would you use it?",
            "Describe the differences between CNN and RNN architectures.",
            "How do you handle imbalanced datasets in classification?"
        ],
        "Hard": [
            "Explain the mathematics behind backpropagation.",
            "How would you optimize a deep learning model for production?",
            "Describe reinforcement learning and provide a real-world example.",
            "Compare attention mechanisms vs traditional sequence-to-sequence models.",
            "How would you design a system to detect anomalies in time-series data?"
        ]
    },
    "Data Scientist": {
        "Easy": [
            "What is the difference between a dataset and a dataframe?",
            "Explain what exploratory data analysis (EDA) is.",
            "What are the different types of statistical distributions?",
            "Describe the purpose of feature scaling in machine learning.",
            "What is the difference between correlation and causation?"
        ],
        "Medium": [
            "How do you implement A/B testing for a web application?",
            "Explain the concept of feature engineering and its importance.",
            "What are the advantages and disadvantages of different cross-validation techniques?",
            "How do you evaluate classification models beyond accuracy?",
            "Describe the steps you would take to handle missing data."
        ],
        "Hard": [
            "Design a pipeline to build a predictive model from raw data.",
            "How would you handle high-dimensional data and explain dimensionality reduction techniques?",
            "Explain time series analysis and ARIMA models.",
            "How do you approach feature selection for high-dimensional datasets?",
            "Describe strategies for dealing with big data and distributed computing."
        ]
    },
    "Software Developer": {
        "Easy": [
            "What are the main principles of object-oriented programming?",
            "Explain the difference between a class and an object.",
            "What is version control and why is it important?",
            "Describe the SOLID principles in software design.",
            "What is the difference between compiled and interpreted languages?"
        ],
        "Medium": [
            "Explain design patterns and provide examples of common ones.",
            "How do you design a scalable REST API?",
            "What is the difference between SQL and NoSQL databases?",
            "Describe the microservices architecture pattern.",
            "How would you optimize a database query for performance?"
        ],
        "Hard": [
            "Design a distributed system that handles millions of requests per second.",
            "Explain the CAP theorem and its implications.",
            "How would you implement caching strategies in a large-scale system?",
            "Describe how to achieve high availability and fault tolerance.",
            "Design a rate limiting system for an API."
        ]
    },
    "Frontend Developer": {
        "Easy": [
            "What is the difference between HTML, CSS, and JavaScript?",
            "Explain what the DOM (Document Object Model) is.",
            "What is responsive design and why is it important?",
            "Describe the difference between var, let, and const in JavaScript.",
            "What is the purpose of CSS flexbox?"
        ],
        "Medium": [
            "How do you optimize website performance and reduce load time?",
            "Explain CSS Grid vs Flexbox and when to use each.",
            "What is AJAX and how does it work?",
            "Describe the virtual DOM and how React uses it.",
            "How do you handle state management in a complex application?"
        ],
        "Hard": [
            "Design a single-page application architecture from scratch.",
            "How would you implement server-side rendering vs client-side rendering?",
            "Explain the performance implications of different rendering strategies.",
            "How do you implement secure authentication in a frontend application?",
            "Design a progressive web app (PWA) with offline capabilities."
        ]
    },
    "Backend Developer": {
        "Easy": [
            "What is a RESTful API and what are its principles?",
            "Explain the difference between authentication and authorization.",
            "What is the purpose of middleware in web applications?",
            "Describe the HTTP request/response cycle.",
            "What is database normalization?"
        ],
        "Medium": [
            "How do you implement caching to improve performance?",
            "Explain the differences between SQL and NoSQL databases.",
            "What are the best practices for API versioning?",
            "Describe how to implement rate limiting.",
            "How do you handle concurrency in a web application?"
        ],
        "Hard": [
            "Design a distributed caching system.",
            "How would you implement database replication and sharding?",
            "Explain eventual consistency and how to handle it.",
            "Design a message queue system for asynchronous processing.",
            "How would you optimize database queries for complex reporting?"
        ]
    }
}

# load API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


def _call_openai(prompt: str, max_tokens: int = 500, temperature: float = 0.7):
    """Helper to call the OpenAI ChatCompletion API and return text."""
    try:
        # updated syntax for openai >=1.0
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        # the response object structure may differ slightly from pre-v1
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Log error and return empty for fallback
        print(f"OpenAI request failed: {e}")
        return ""


def generate_questions(role: str, difficulty: str, count: int = 5) -> list:
    """Ask the LLM to produce a list of interview questions.

    Falls back to mock questions if API is unavailable.
    """
    prompt = (
        f"Generate {count} distinct interview questions \n"
        f"for a {role} position at {difficulty} difficulty level.\n"
        "Return the questions as a JSON array of strings only."
    )
    text = _call_openai(prompt, max_tokens=500)
    try:
        if text:  # only if API call succeeded
            questions = json.loads(text)
            return [str(q) for q in questions]
    except Exception:
        pass
    
    # Fallback to mock questions
    if role in MOCK_QUESTIONS and difficulty in MOCK_QUESTIONS[role]:
        bank = MOCK_QUESTIONS[role][difficulty]
        return random.sample(bank, min(count, len(bank)))
    
    return [
        f"Tell us about your experience with {role}.",
        "Describe a challenging project you worked on.",
        "How do you approach problem-solving?",
        "What are your strengths and areas for improvement?",
        "Why are you interested in this position?"
    ]


def evaluate_answer(question: str, answer: str, role: str = None, difficulty: str = None) -> dict:
    """Send a single question+answer to the LLM and get evaluation details.

    Falls back to mock evaluation if API is unavailable.
    """
    role_info = f"Role: {role}, Difficulty: {difficulty}\n" if role and difficulty else ""
    prompt = (
        f"{role_info}You are an expert technical interviewer. "
        f"The candidate was asked the following question:\n\n"
        f"{question}\n\n"
        "Their answer was:\n\n"
        f"{answer}\n\n"
        "Evaluate the response on a scale of 0 to 10 and return a JSON object with the "
        "following keys: score, strengths, weaknesses, suggestions, model_answer. "
        "The model_answer field should provide a sample high-quality response."
    )
    text = _call_openai(prompt, max_tokens=400)
    try:
        if text:  # only if API call succeeded
            result = json.loads(text)
            return result
    except Exception:
        pass
    
    # Fallback mock evaluation based on answer length and content
    answer_length = len(answer.split())
    has_examples = any(kw in answer.lower() for kw in ['example', 'for instance', 'such as'])
    has_detail = any(kw in answer.lower() for kw in ['because', 'reason', 'specifically'])
    
    base_score = min(10, max(1, (answer_length // 5)))
    if has_examples:
        base_score = min(10, base_score + 2)
    if has_detail:
        base_score = min(10, base_score + 1)
    
    score = max(4, base_score)  # minimum 4 for any attempt
    
    return {
        "score": score,
        "strengths": "Your answer demonstrates understanding of the key concepts and you provided relevant details." if answer_length > 20 else "You addressed the question but could provide more detail.",
        "weaknesses": "The answer could benefit from concrete examples." if not has_examples else "Consider elaborating on edge cases.",
        "suggestions": "Include real-world examples and explain your reasoning with more depth. Discuss trade-offs and alternatives when applicable.",
        "model_answer": f"A strong answer would explain the core concept, provide examples, discuss trade-offs, and relate the answer to real-world scenarios in {role}."
    }


def generate_final_feedback(evaluations: list, role: str, difficulty: str) -> dict:
    """Compile a summary feedback report from individual evaluations."""
    prompt = (
        f"You are an AI interview coach. A candidate answered the following "
        f"questions for a {role} position at {difficulty} difficulty. "
        "Below is a JSON array where each element has 'question', 'answer' and "
        "the evaluation result (score, strengths, weaknesses, suggestions).\n\n"
        f"{json.dumps(evaluations, indent=2)}\n\n"
        "Provide a summary JSON object containing:\n"
        "total_questions, question_scores (array), overall_score, strengths, weaknesses, "
        "suggestions, study_areas.\n"
        "Respond strictly with JSON."
    )
    text = _call_openai(prompt, max_tokens=1000)
    try:
        if text:
            feedback = json.loads(text)
            return feedback
    except Exception:
        pass
    
    # Fallback aggregation
    scores = [ev.get('score', 0) for ev in evaluations]
    overall = sum(scores) / len(scores) if scores else 0
    
    return {
        "total_questions": len(evaluations),
        "question_scores": scores,
        "overall_score": round(overall, 1),
        "strengths": "You demonstrated solid understanding of the key concepts. Your answers showed good depth and provided practical examples where appropriate.",
        "weaknesses": "Some answers lacked concrete examples or deeper technical reasoning. Consider preparing more about system design and architectural patterns.",
        "suggestions": "Practice explaining complex concepts in simpler terms. Prepare concrete examples from your past projects. Focus on discussing trade-offs and alternative approaches.",
        "study_areas": f"Focus on: Advanced {role} concepts, system design fundamentals, code optimization techniques, and best practices in your field."
    }
