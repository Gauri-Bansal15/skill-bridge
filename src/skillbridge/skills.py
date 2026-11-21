"""A small skill taxonomy.

It is used by the offline demo engine and to double-check what the language
model claims. Keys are the canonical skill names shown to the user, values are
the spellings we also accept.
"""
from __future__ import annotations

import re
from functools import lru_cache

SKILLS: dict[str, list[str]] = {
    # languages
    "Python": ["python"],
    "SQL": ["sql", "mysql", "postgresql", "sqlite"],
    "Java": ["java"],
    "C++": ["c++"],
    "JavaScript": ["javascript", "js", "es6"],
    "TypeScript": ["typescript"],
    # data and ML
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "neural network", "neural networks", "cnn"],
    "TensorFlow": ["tensorflow", "keras"],
    "PyTorch": ["pytorch"],
    "NLP": ["nlp", "natural language processing"],
    "data analysis": ["data analysis", "data analytics", "exploratory data analysis", "eda", "result analysis"],
    "data visualization": ["data visualization", "data visualisation", "matplotlib", "seaborn", "plotly"],
    "statistics": ["statistics", "statistical analysis"],
    "Excel": ["excel", "ms excel", "microsoft excel"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    # web
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node.js", "nodejs", "node"],
    "REST APIs": ["rest api", "rest apis", "restful", "restful api", "restful apis"],
    "Flask": ["flask"],
    "Streamlit": ["streamlit"],
    "MongoDB": ["mongodb"],
    # tools and cloud
    "Git": ["git", "github"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Linux": ["linux"],
}


@lru_cache(maxsize=None)
def _pattern(alias: str) -> re.Pattern:
    # An alias counts only when it is not glued to other letters/digits,
    # so "Java" does not match inside "JavaScript".
    return re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(alias) + r"(?![A-Za-z0-9+#])", re.IGNORECASE)


def mentions(text: str, skill: str) -> bool:
    """True if `text` mentions `skill` under any accepted spelling."""
    return any(_pattern(a).search(text) for a in SKILLS.get(skill, [skill.lower()]))


def find_skills(text: str) -> list[str]:
    """Canonical skills mentioned in `text`, in taxonomy order."""
    return [s for s in SKILLS if mentions(text, s)]


def canonical(name: str) -> str:
    """Map any spelling of a skill ('REST API', 'ml') to the canonical name, lower-cased."""
    found = find_skills(name)
    return (found[0] if found else name.strip()).lower()
