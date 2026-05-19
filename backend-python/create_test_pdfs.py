"""
create_test_pdfs.py  — Generate 30 student PDFs + 1 model answer PDF for testing.

Topic  : Artificial Intelligence
Sections: Definition / Body / Conclusion
Marks  : Definition=2, Body=3, Conclusion=2  (total 7)

Typed PDFs  : T01-T15  (real text layer, PyMuPDF)
Scanned PDFs: S16-S30  (text rendered onto image + noise, embedded in PDF)

Run from backend-python/:
    python create_test_pdfs.py
"""

import os, math, textwrap
import fitz                    # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
OUT_DIR     = os.path.join(SCRIPT_DIR, "test_data")
TYPED_DIR   = os.path.join(OUT_DIR, "typed")
SCANNED_DIR = os.path.join(OUT_DIR, "scanned")

for d in (OUT_DIR, TYPED_DIR, SCANNED_DIR):
    os.makedirs(d, exist_ok=True)

# Arial font for image-based PDFs (scanned simulation)
FONT_PATH = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"

# ---------------------------------------------------------------------------
# Model answer text
# ---------------------------------------------------------------------------
MODEL = {
    "Definition": (
        "Artificial Intelligence (AI) is the simulation of human intelligence processes by "
        "machines, especially computer systems. These processes include learning (the acquisition "
        "of information and rules for using it), reasoning (using rules to reach approximate or "
        "definite conclusions), and self-correction. AI enables machines to perform tasks that "
        "typically require human intelligence, such as visual perception, speech recognition, "
        "decision-making, and language translation."
    ),
    "Body": (
        "AI applications span multiple domains. Machine Learning (ML) is a subset of AI where "
        "systems learn from data without being explicitly programmed. Deep Learning uses neural "
        "networks with many layers to recognise patterns. Natural Language Processing (NLP) enables "
        "machines to understand and generate human language. Computer Vision allows machines to "
        "interpret visual information. Robotics integrates AI for autonomous physical actions. "
        "Key AI techniques include supervised learning, unsupervised learning, reinforcement "
        "learning, and transfer learning. AI is used in healthcare for diagnostics, in finance "
        "for fraud detection, in transportation for self-driving cars, and in education for "
        "personalised learning systems."
    ),
    "Conclusion": (
        "Artificial Intelligence represents a transformative technology that is reshaping "
        "industries and society. While AI offers immense benefits in automation, efficiency, "
        "and problem-solving, it also raises ethical concerns about privacy, bias, job "
        "displacement, and autonomous decision-making. Responsible AI development requires "
        "transparency, fairness, and accountability. The future of AI depends on advancing "
        "research in explainable AI, general AI, and quantum AI while ensuring human-centric "
        "design principles."
    ),
}

# ---------------------------------------------------------------------------
# 30 Student profiles
# Expected grade reference (not stored in PDF):
#   T01 O, T02 A+, T03 A, T04 A, T05 A, T06 B+, T07 B+, T08 B,
#   T09 C, T10 B, T11 C, T12 F, T13 F, T14 B, T15 B+
#   S16 A, S17 B+, S18 C, S19 A, S20 B+, S21 C, S22 B, S23 C,
#   S24 ?, S25 A, S26 B+, S27 B, S28 C, S29 C, S30 B+
# ---------------------------------------------------------------------------
STUDENTS = [
    # ---- TYPED ---------------------------------------------------------------
    {
        "id": "T01", "label": "Excellent", "typed": True,
        "Definition": (
            "Artificial Intelligence (AI) is the field of computer science dedicated to "
            "creating systems that can perform tasks requiring human intelligence. It includes "
            "processes like learning, reasoning, problem-solving, and self-correction. "
            "AI systems can perceive their environment and take actions to maximise their "
            "chance of achieving goals, enabling machines to handle tasks such as visual "
            "perception, speech recognition, decision-making, and natural language understanding."
        ),
        "Body": (
            "AI encompasses several subfields. Machine Learning allows systems to learn "
            "from data without explicit programming. Deep Learning uses multi-layered neural "
            "networks to recognise complex patterns in images, speech, and text. Natural "
            "Language Processing (NLP) enables machines to understand and generate human "
            "language, powering chatbots and translation tools. Computer Vision interprets "
            "visual data for applications like face recognition and autonomous vehicles. "
            "Core techniques include supervised learning (labelled data), unsupervised learning "
            "(unlabelled data), and reinforcement learning (reward-based). AI is transforming "
            "healthcare (diagnostics), finance (fraud detection), transportation (self-driving "
            "cars), and education (personalised learning)."
        ),
        "Conclusion": (
            "AI is a transformative technology reshaping industries globally. Its benefits "
            "include automation, improved efficiency, and enhanced problem-solving capabilities. "
            "However, it also presents challenges: ethical concerns around privacy, algorithmic "
            "bias, and job displacement require careful consideration. Responsible AI development "
            "must ensure transparency, fairness, and accountability. Future research in "
            "explainable AI, artificial general intelligence, and quantum AI will determine "
            "the long-term impact of this technology on humanity."
        ),
    },
    {
        "id": "T02", "label": "Very Good", "typed": True,
        "Definition": (
            "Artificial Intelligence is the ability of machines to simulate human-like "
            "intelligence including learning, reasoning, and self-correction. AI systems "
            "can perform tasks such as speech recognition, visual perception, and language "
            "translation that traditionally required human intelligence."
        ),
        "Body": (
            "Machine Learning is a key branch of AI where systems learn from data. Deep "
            "Learning uses neural networks to detect patterns. NLP allows computers to "
            "understand language, enabling chatbots and translators. Computer Vision handles "
            "image and video interpretation. Supervised, unsupervised, and reinforcement "
            "learning are the main ML techniques. AI has wide applications: diagnostics in "
            "healthcare, fraud detection in banking, and self-driving vehicles in transportation."
        ),
        "Conclusion": (
            "AI is transforming every major industry by automating tasks and improving "
            "decision-making. While the benefits are enormous, concerns about job displacement, "
            "bias, and privacy must be addressed. Responsible and transparent AI development "
            "is essential for a positive future impact on society."
        ),
    },
    {
        "id": "T03", "label": "Good", "typed": True,
        "Definition": (
            "AI stands for Artificial Intelligence. It is a branch of computer science that "
            "makes machines intelligent by enabling them to learn, reason, and make decisions. "
            "AI can do tasks like image recognition and language translation."
        ),
        "Body": (
            "The main types of AI include Machine Learning, where machines learn from data, "
            "and Deep Learning, which uses neural networks. NLP helps computers understand "
            "human language. AI is used in healthcare for medical imaging, in finance for "
            "detecting fraud, and in self-driving cars. Reinforcement learning and supervised "
            "learning are important AI techniques."
        ),
        "Conclusion": (
            "Artificial Intelligence is very important for the modern world. It helps in "
            "automation and solving complex problems. However, ethical issues like privacy "
            "and job displacement must be considered. Responsible development of AI is "
            "necessary for a better future."
        ),
    },
    {
        "id": "T04", "label": "Good-DiffVocab", "typed": True,
        "Definition": (
            "AI refers to computer programmes that can think and act like humans. These "
            "systems can process information, draw conclusions from data, and correct "
            "themselves over time. They handle jobs that normally need a human brain, "
            "such as understanding spoken words or identifying objects in pictures."
        ),
        "Body": (
            "Under the AI umbrella, statistical learning systems (often called ML) train "
            "on examples to make predictions. Layered computational graphs (deep networks) "
            "are especially good at recognising images and speech. Text-processing pipelines "
            "help computers read and write human language. Intelligent robots use vision and "
            "planning to operate in the physical world. Doctors use AI to spot diseases "
            "in scans; banks use it to catch suspicious transactions; car makers use it "
            "to build vehicles that steer themselves."
        ),
        "Conclusion": (
            "Intelligent systems are reshaping how work gets done across every sector. "
            "The gains in speed and accuracy are remarkable, but questions of fairness, "
            "accountability, and worker impact cannot be ignored. Building AI that is "
            "explainable and aligned with human values will be the central challenge "
            "of the coming decades."
        ),
    },
    {
        "id": "T05", "label": "Concise-Correct", "typed": True,
        "Definition": (
            "AI is the simulation of human intelligence by machines, covering learning, "
            "reasoning, and self-correction. Machines with AI can do tasks like speech "
            "recognition and decision-making."
        ),
        "Body": (
            "Key branches: Machine Learning trains on data; Deep Learning uses neural "
            "networks; NLP handles language; Computer Vision handles images. Main techniques "
            "are supervised, unsupervised, and reinforcement learning. Applications: "
            "healthcare diagnostics, fraud detection, self-driving cars."
        ),
        "Conclusion": (
            "AI is transformative but raises ethical issues around bias, privacy, and jobs. "
            "Responsible, transparent AI is needed for positive societal impact."
        ),
    },
    {
        "id": "T06", "label": "Average", "typed": True,
        "Definition": (
            "Artificial Intelligence is when computers are made to think like humans. "
            "It can learn and make decisions. AI is used in many applications today."
        ),
        "Body": (
            "There are different types of AI. Machine Learning is one type where "
            "the computer learns from data. Deep learning is another type. "
            "NLP is for language. AI is used in hospitals and banks. "
            "There are also self-driving cars that use AI."
        ),
        "Conclusion": (
            "AI is important and has many uses. It also has some problems like ethical "
            "issues. We need to be careful when using AI."
        ),
    },
    {
        "id": "T07", "label": "Wordy-Repetitive", "typed": True,
        "Definition": (
            "Artificial Intelligence, commonly known as AI, is basically the intelligence "
            "demonstrated by machines. In other words, AI is all about making machines "
            "intelligent. Artificial Intelligence makes machines intelligent so that they "
            "can think and learn just like humans. So AI means machine intelligence, and "
            "this machine intelligence is used in many many different ways."
        ),
        "Body": (
            "In terms of the types and applications of Artificial Intelligence, there are "
            "many types. Machine Learning is a type of AI. Machine Learning is very important. "
            "Deep Learning is also a type and Deep Learning uses neural networks. NLP stands "
            "for Natural Language Processing and NLP is used for language. AI applications "
            "include healthcare and healthcare uses AI for diagnosis. Finance also uses AI "
            "and finance uses AI for fraud detection. Self-driving cars also use AI. "
            "AI is used everywhere in today's world in many different applications."
        ),
        "Conclusion": (
            "In conclusion, AI is a very important technology. AI has many benefits and AI "
            "also has challenges. The challenges of AI include ethical concerns. We should "
            "use AI responsibly. Responsible AI is very important. AI will be very important "
            "in the future and the future of AI is bright."
        ),
    },
    {
        "id": "T08", "label": "Bullet-Points", "typed": True,
        "Definition": (
            "- AI = Artificial Intelligence\n"
            "- Simulation of human intelligence by machines\n"
            "- Includes: learning, reasoning, self-correction\n"
            "- Tasks: speech recognition, visual perception, decision-making"
        ),
        "Body": (
            "- Machine Learning: learns from data without explicit programming\n"
            "- Deep Learning: multi-layer neural networks for pattern recognition\n"
            "- NLP: machines understand and generate language\n"
            "- Computer Vision: interprets images and video\n"
            "- Applications:\n"
            "   * Healthcare: diagnostics\n"
            "   * Finance: fraud detection\n"
            "   * Transport: self-driving cars\n"
            "- Techniques: supervised, unsupervised, reinforcement learning"
        ),
        "Conclusion": (
            "- AI is transformative and reshapes industries\n"
            "- Benefits: automation, efficiency, decision-making\n"
            "- Concerns: privacy, bias, job displacement\n"
            "- Need: transparent, fair, accountable AI development"
        ),
    },
    {
        "id": "T09", "label": "Below-Average", "typed": True,
        "Definition": (
            "AI is computer technology that helps machines do smart things. "
            "It is used in phones and computers."
        ),
        "Body": (
            "Machine learning and deep learning are parts of AI. "
            "AI helps in hospitals. There are some algorithms in AI. "
            "Siri and Alexa use AI."
        ),
        "Conclusion": (
            "AI is very useful. It can do many things. But there are some bad things too."
        ),
    },
    {
        "id": "T10", "label": "Keyword-Stuffing", "typed": True,
        "Definition": (
            "AI artificial intelligence machine learning deep learning neural network "
            "learning reasoning self-correction intelligence machines computer intelligence "
            "artificial system AI intelligence learning AI machines learning artificial "
            "intelligence AI AI AI machine learning deep learning neural network AI systems."
        ),
        "Body": (
            "Machine learning AI deep learning neural network NLP natural language "
            "processing computer vision reinforcement learning supervised learning "
            "unsupervised learning AI machine learning deep learning AI neural networks "
            "NLP computer vision AI machine learning supervised reinforcement learning "
            "AI healthcare finance fraud detection AI autonomous self-driving AI ML DL NLP."
        ),
        "Conclusion": (
            "AI artificial intelligence transformative technology AI ethics bias privacy "
            "AI responsible AI transparent AI explainable AI general AI quantum AI "
            "AI AI AI responsible transparent accountable fairness AI future AI AI AI "
            "AI artificial intelligence machine learning deep learning neural network."
        ),
    },
    {
        "id": "T11", "label": "Weak", "typed": True,
        "Definition": "Artificial Intelligence is when machines can think and learn.",
        "Body": "AI has machine learning and deep learning. It is used in hospitals and cars.",
        "Conclusion": "AI is useful but has problems.",
    },
    {
        "id": "T12", "label": "Very-Weak", "typed": True,
        "Definition": "AI means computers are smart.",
        "Body": "Machine learning.",
        "Conclusion": "AI is good.",
    },
    {
        "id": "T13", "label": "Off-Topic", "typed": True,
        "Definition": (
            "The water cycle describes how water evaporates from the surface of the Earth, "
            "rises into the atmosphere, cools and condenses into clouds, and falls back to "
            "the surface as precipitation. This cycle is essential for life on Earth."
        ),
        "Body": (
            "The main stages of the water cycle are evaporation, condensation, precipitation, "
            "and collection. Evaporation occurs when liquid water is heated by the sun and "
            "turns into water vapour. This vapour rises into the atmosphere and cools to form "
            "clouds through condensation. Precipitation falls as rain or snow and is collected "
            "in rivers, lakes, and oceans, restarting the cycle."
        ),
        "Conclusion": (
            "The water cycle is fundamental to all ecosystems on Earth. It regulates "
            "temperature, distributes fresh water, and supports plant and animal life. "
            "Human activities like deforestation and pollution can disrupt the water cycle."
        ),
    },
    {
        "id": "T14", "label": "Blank-Body", "typed": True,
        "Definition": (
            "Artificial Intelligence is the simulation of human intelligence processes by "
            "computer systems, including learning, reasoning, and self-correction. "
            "It enables tasks like speech recognition, visual perception, and decision-making."
        ),
        "Body": "",  # intentionally blank
        "Conclusion": (
            "AI is reshaping industries and society. Ethical concerns around bias and "
            "privacy must be addressed through responsible, transparent AI development."
        ),
    },
    {
        "id": "T15", "label": "Mixed-Quality", "typed": True,
        "Definition": (
            "Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
            "It includes learning, reasoning, and self-correction capabilities. AI can perform "
            "tasks like speech recognition, visual perception, and complex decision-making."
        ),
        "Body": "AI stuff. Machine learning. Also deep learning. Healthcare and stuff.",
        "Conclusion": (
            "AI is a transformative force reshaping industries globally. Ethical considerations "
            "including privacy, bias, job displacement, and accountability must guide "
            "responsible AI development. Future advances in explainable AI and general AI "
            "will determine technology's long-term societal impact."
        ),
    },

    # ---- SCANNED (image-in-PDF) ----------------------------------------------
    {
        "id": "S16", "label": "Good-CleanScan", "typed": False, "noise": "low",
        "Definition": (
            "Artificial Intelligence is the branch of computer science that enables machines "
            "to perform tasks that would normally require human intelligence. This includes "
            "learning from experience, understanding language, recognising patterns, and "
            "making decisions. AI systems use algorithms and data to simulate intelligent behaviour."
        ),
        "Body": (
            "AI includes Machine Learning where systems learn from data, Deep Learning "
            "which uses layered neural networks for complex pattern recognition, and NLP "
            "which processes human language. Computer Vision allows machines to interpret "
            "images. Applications include medical diagnosis in healthcare, fraud detection "
            "in finance, and autonomous vehicles in transportation. Techniques include "
            "supervised, unsupervised, and reinforcement learning."
        ),
        "Conclusion": (
            "AI is transforming industries and offers significant benefits in automation "
            "and efficiency. However, challenges such as bias, privacy violations, and "
            "job displacement must be managed. Ethical and responsible AI development "
            "with transparency and fairness is crucial for positive societal outcomes."
        ),
    },
    {
        "id": "S17", "label": "Average-CleanScan", "typed": False, "noise": "low",
        "Definition": (
            "AI is making computers do intelligent things like humans. It can learn from "
            "data and make decisions. AI is used in many applications today."
        ),
        "Body": (
            "Machine Learning and Deep Learning are types of AI. NLP handles language "
            "understanding. AI is used in hospitals for diagnosis and in banks for fraud. "
            "Self-driving cars also use AI technology."
        ),
        "Conclusion": (
            "AI is very important today. It has benefits but also has ethical problems "
            "like privacy and bias. We should develop AI responsibly."
        ),
    },
    {
        "id": "S18", "label": "Weak-CleanScan", "typed": False, "noise": "low",
        "Definition": "AI is intelligent computer systems.",
        "Body": "Machine learning is part of AI. Used in healthcare.",
        "Conclusion": "AI is good but has problems.",
    },
    {
        "id": "S19", "label": "Good-MedNoise", "typed": False, "noise": "medium",
        "Definition": (
            "Artificial Intelligence enables machines to simulate human intelligence "
            "including learning, reasoning, and self-correction. It allows computers "
            "to perform tasks like speech recognition, visual perception, and translation."
        ),
        "Body": (
            "Key subfields of AI include Machine Learning (systems learn from data), "
            "Deep Learning (multi-layer neural networks), NLP (language processing), "
            "and Computer Vision (image interpretation). Main techniques are supervised, "
            "unsupervised, and reinforcement learning. AI applications span healthcare "
            "(diagnostics), finance (fraud detection), and autonomous vehicles."
        ),
        "Conclusion": (
            "AI is a transformative technology with wide industrial impact. Ethical "
            "challenges like bias, privacy, and job displacement must be addressed "
            "through responsible and transparent AI development practices."
        ),
    },
    {
        "id": "S20", "label": "Average-MedNoise", "typed": False, "noise": "medium",
        "Definition": (
            "AI is technology that makes machines think and learn like humans. "
            "It is used in many modern applications."
        ),
        "Body": (
            "Machine learning trains computers using data. Deep learning uses neural networks. "
            "NLP is for language. AI is applied in hospitals and self-driving cars."
        ),
        "Conclusion": "AI is useful but has ethical issues like bias and privacy.",
    },
    {
        "id": "S21", "label": "Weak-MedNoise", "typed": False, "noise": "medium",
        "Definition": "Artificial intelligence makes machines smart.",
        "Body": "Machine learning and neural networks.",
        "Conclusion": "AI has benefits and challenges.",
    },
    {
        "id": "S22", "label": "Good-HeavyNoise", "typed": False, "noise": "heavy",
        "Definition": (
            "AI (Artificial Intelligence) refers to machines simulating human intelligence. "
            "This includes learning from data, logical reasoning, and self-correction. "
            "AI enables speech recognition, image analysis, and decision-making."
        ),
        "Body": (
            "Machine Learning, Deep Learning, NLP, and Computer Vision are AI branches. "
            "Supervised learning uses labelled data; unsupervised learning finds hidden "
            "patterns; reinforcement learning uses rewards. Applications: medical imaging "
            "in healthcare, anomaly detection in finance, path planning in robotics "
            "and autonomous vehicles."
        ),
        "Conclusion": (
            "AI is reshaping society. Benefits include efficiency and automation. "
            "Ethical concerns: algorithmic bias, data privacy, and workforce disruption. "
            "Responsible AI needs explainability, fairness, and human oversight."
        ),
    },
    {
        "id": "S23", "label": "Average-HeavyNoise", "typed": False, "noise": "heavy",
        "Definition": "AI is when machines can learn and make decisions like humans.",
        "Body": (
            "Deep learning and machine learning are part of AI. NLP is for language tasks. "
            "AI is used in healthcare and transport."
        ),
        "Conclusion": "AI is important but has problems with ethics and privacy.",
    },
    {
        "id": "S24", "label": "Cheating-Copied", "typed": False, "noise": "low",
        # Nearly verbatim copy of model — high semantic + keyword density
        "Definition": (
            "Artificial Intelligence (AI) is the simulation of human intelligence processes by "
            "machines, especially computer systems. These processes include learning, reasoning, "
            "and self-correction. AI enables machines to perform tasks that typically require "
            "human intelligence, such as visual perception, speech recognition, and decision-making."
        ),
        "Body": (
            "AI applications span multiple domains. Machine Learning (ML) is a subset of AI where "
            "systems learn from data without being explicitly programmed. Deep Learning uses neural "
            "networks with many layers to recognise patterns. Natural Language Processing (NLP) "
            "enables machines to understand and generate human language. Computer Vision allows "
            "machines to interpret visual information. Key techniques include supervised learning, "
            "unsupervised learning, and reinforcement learning. AI is used in healthcare for "
            "diagnostics, in finance for fraud detection, and in transportation for self-driving cars."
        ),
        "Conclusion": (
            "Artificial Intelligence represents a transformative technology reshaping industries. "
            "While AI offers immense benefits in automation, efficiency, and problem-solving, "
            "it raises ethical concerns about privacy, bias, job displacement, and autonomous "
            "decision-making. Responsible AI requires transparency, fairness, and accountability."
        ),
    },
    {
        "id": "S25", "label": "Alt-Vocab", "typed": False, "noise": "low",
        "Definition": (
            "Machine cognition — the capacity of computers to replicate mental faculties "
            "such as pattern recognition, logical inference, and adaptive learning — is the "
            "core idea behind AI. Systems built on these principles handle challenges like "
            "decoding spoken words, identifying objects in photos, and selecting optimal actions."
        ),
        "Body": (
            "Several technical disciplines fall under the AI umbrella. Statistical modelling "
            "from large datasets (machine learning) is foundational. Stacked perceptron "
            "architectures (deep networks) excel at high-dimensional perception tasks. "
            "Computational linguistics (NLP) bridges human and machine communication. "
            "Reward-guided trial and error (reinforcement learning) trains agents without "
            "labelled data. These methods power radiology assistants, transaction monitoring "
            "systems, and highway autopilots."
        ),
        "Conclusion": (
            "Synthetic cognition is the defining technological shift of our era. The "
            "productivity gains are real, but so are the risks: skewed training sets encode "
            "social inequity; ubiquitous surveillance erodes privacy; labour displacement "
            "strains social contracts. Ensuring algorithmic accountability and interpretability "
            "is the prerequisite for harnessing these systems safely."
        ),
    },
    {
        "id": "S26", "label": "Abbreviations", "typed": False, "noise": "medium",
        "Definition": (
            "AI = Artificial Intelligence. It simulates human intel in machines incl. "
            "learning, reasoning & self-correction. Used for ASR (auto speech recog.), "
            "CV (computer vision) & NLU (natural lang. understanding)."
        ),
        "Body": (
            "Subfields: ML (Machine Learning) — learns from data; DL (Deep Learning) — "
            "multi-layer NNs; NLP — text+speech processing; CV — image recognition. "
            "Algos: SL (supervised), UL (unsupervised), RL (reinforcement). "
            "Apps: healthcare dx, fin fraud det., AV (autonomous vehicles)."
        ),
        "Conclusion": (
            "AI is transformative. Ethical issues: bias, privacy, job loss. Need: XAI "
            "(explainable AI), responsible dev, accountability. Future: AGI, quantum AI."
        ),
    },
    {
        "id": "S27", "label": "Bullets-Scanned", "typed": False, "noise": "low",
        "Definition": (
            "* AI = simulation of human intelligence in machines\n"
            "* Covers learning, reasoning, self-correction\n"
            "* Applications: speech recognition, visual perception, decision-making"
        ),
        "Body": (
            "* ML: learns from data without explicit programming\n"
            "* DL: neural networks detect complex patterns\n"
            "* NLP: machines understand language\n"
            "* Computer Vision: image/video interpretation\n"
            "* Techniques: supervised, unsupervised, reinforcement learning\n"
            "* Uses: healthcare, finance, autonomous vehicles"
        ),
        "Conclusion": (
            "* AI reshapes all industries\n"
            "* Benefits: automation, efficiency\n"
            "* Risks: bias, privacy, job displacement\n"
            "* Responsible, transparent AI is required"
        ),
    },
    {
        "id": "S28", "label": "Mixed-Lang", "typed": False, "noise": "medium",
        "Definition": (
            "AI matlab Artificial Intelligence. It is the process jisme computers ko "
            "human jaise sochne ki capability di jati hai. Learning, reasoning aur "
            "self-correction AI ke main processes hain."
        ),
        "Body": (
            "Machine Learning is ek subset of AI jahan system data se seekhta hai "
            "bina explicitly program kiye. Deep Learning uses neural networks. "
            "NLP helps in language understanding. Healthcare mein AI diagnostic ke "
            "liye use hota hai. Finance mein fraud detection ke liye."
        ),
        "Conclusion": (
            "AI ek transformative technology hai. Iske benefits hain jaise automation "
            "aur efficiency. But ethical issues bhi hain like privacy aur job displacement. "
            "Responsible AI development zaruri hai."
        ),
    },
    {
        "id": "S29", "label": "Only-Definition", "typed": False, "noise": "low",
        "Definition": (
            "Artificial Intelligence is the simulation of human intelligence processes by "
            "machines. It includes learning from experience, reasoning logically, and "
            "self-correction. AI enables machines to perform tasks like visual perception, "
            "speech recognition, decision-making, and language translation."
        ),
        "Body": "",   # blank — student ran out of time
        "Conclusion": "",  # blank
    },
    {
        "id": "S30", "label": "No-Headers", "typed": False, "noise": "low",
        # Student wrote one continuous answer with no section labels
        "Definition": (
            "Artificial Intelligence is the simulation of human intelligence in machines "
            "covering learning, reasoning, and self-correction. It enables speech recognition, "
            "visual perception, and decision-making. AI subfields include Machine Learning "
            "(learning from data), Deep Learning (neural networks), NLP (language processing), "
            "and Computer Vision (image analysis). Supervised, unsupervised, and reinforcement "
            "learning are key techniques. AI is used in healthcare diagnostics, financial fraud "
            "detection, and autonomous vehicles. While transformative, AI raises ethical concerns "
            "about privacy, bias, and job displacement requiring transparent, responsible development."
        ),
        "Body": (
            "Artificial Intelligence is the simulation of human intelligence in machines "
            "covering learning, reasoning, and self-correction. It enables speech recognition, "
            "visual perception, and decision-making. AI subfields include Machine Learning "
            "(learning from data), Deep Learning (neural networks), NLP (language processing), "
            "and Computer Vision (image analysis). Supervised, unsupervised, and reinforcement "
            "learning are key techniques. AI is used in healthcare diagnostics, financial fraud "
            "detection, and autonomous vehicles. While transformative, AI raises ethical concerns "
            "about privacy, bias, and job displacement requiring transparent, responsible development."
        ),
        "Conclusion": (
            "Artificial Intelligence is the simulation of human intelligence in machines "
            "covering learning, reasoning, and self-correction. It enables speech recognition, "
            "visual perception, and decision-making. AI subfields include Machine Learning "
            "(learning from data), Deep Learning (neural networks), NLP (language processing), "
            "and Computer Vision (image analysis). Supervised, unsupervised, and reinforcement "
            "learning are key techniques. AI is used in healthcare diagnostics, financial fraud "
            "detection, and autonomous vehicles. While transformative, AI raises ethical concerns "
            "about privacy, bias, and job displacement requiring transparent, responsible development."
        ),
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_typed_pdf(out_path: str, sections: dict):
    """Create a typed (text-layer) PDF using PyMuPDF."""
    doc  = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    y = 60
    # Header
    page.insert_text((50, y), "Student Answer Sheet", fontsize=14, fontname="helv")
    y += 25
    page.insert_text((50, y), "Subject: Artificial Intelligence", fontsize=10, fontname="helv")
    y += 30

    for section, text in sections.items():
        if y > 760:
            page = doc.new_page(width=595, height=842)
            y = 60

        # Section heading
        page.insert_text((50, y), f"{section}:", fontsize=12, fontname="helv")
        y += 18

        if not text or not text.strip():
            page.insert_text((60, y), "(No answer provided)", fontsize=10, fontname="helv")
            y += 18
        else:
            wrapped = textwrap.wrap(text.replace("\n", " "), width=85)
            for line in wrapped:
                if y > 790:
                    page = doc.new_page(width=595, height=842)
                    y = 60
                page.insert_text((60, y), line, fontsize=10, fontname="helv")
                y += 15
        y += 12

    doc.save(out_path)
    doc.close()


def _get_font(size: int, bold: bool = False):
    try:
        fp = FONT_BOLD if bold else FONT_PATH
        return ImageFont.truetype(fp, size)
    except Exception:
        return ImageFont.load_default()


def make_scanned_pdf(out_path: str, sections: dict, noise_level: str = "medium"):
    """Create an image-in-PDF to simulate a scanned handwritten sheet."""
    W, H = 1654, 2339  # A4 at 200 DPI
    img  = Image.new("RGB", (W, H), color=(255, 253, 248))
    draw = ImageDraw.Draw(img)

    heading_font = _get_font(36, bold=True)
    section_font = _get_font(30, bold=True)
    body_font    = _get_font(26)

    y = 80
    draw.text((80, y), "Student Answer Sheet", font=heading_font, fill=(10, 10, 60))
    y += 55
    draw.text((80, y), "Subject: Artificial Intelligence", font=body_font, fill=(40, 40, 40))
    y += 60

    for section, text in sections.items():
        if y > H - 200:
            # Flush and start new image (simplified: just continue on same page)
            y = H - 200

        draw.text((80, y), f"{section}:", font=section_font, fill=(20, 20, 140))
        y += 44

        if not text or not text.strip():
            draw.text((100, y), "(No answer provided)", font=body_font, fill=(150, 150, 150))
            y += 36
        else:
            for raw_line in text.split("\n"):
                wrapped = textwrap.wrap(raw_line, width=72) if raw_line.strip() else [""]
                for line in wrapped:
                    if y > H - 80:
                        break
                    draw.text((100, y), line, font=body_font, fill=(20, 20, 20))
                    y += 34
        y += 30

    # Add noise
    arr = np.array(img, dtype=np.float32)
    if noise_level == "low":
        sigma = 6
        speck = 0.003
    elif noise_level == "medium":
        sigma = 16
        speck = 0.012
    else:  # heavy
        sigma = 32
        speck = 0.04

    noise = np.random.normal(0, sigma, arr.shape)
    arr   = np.clip(arr + noise, 0, 255)

    # Salt-and-pepper specks
    mask = np.random.random(arr.shape[:2]) < speck
    arr[mask] = 0
    mask2 = np.random.random(arr.shape[:2]) < speck
    arr[mask2] = 255

    img = Image.fromarray(arr.astype(np.uint8))

    if noise_level in ("medium", "heavy"):
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6 if noise_level == "medium" else 1.1))

    # Embed image in a PDF
    img_bytes_io = __import__("io").BytesIO()
    img.save(img_bytes_io, format="JPEG", quality=85)
    img_bytes = img_bytes_io.getvalue()

    doc  = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(0, 0, 595, 842)
    page.insert_image(rect, stream=img_bytes)
    doc.save(out_path)
    doc.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  GRADX Test PDF Generator")
    print("=" * 60)

    # 1. Model answer
    model_path = os.path.join(OUT_DIR, "model_answer.pdf")
    make_typed_pdf(model_path, MODEL)
    print(f"[OK] Model answer: {model_path}")

    # 2. Student PDFs
    typed_count   = 0
    scanned_count = 0

    for s in STUDENTS:
        sid   = s["id"]
        label = s["label"]
        typed = s["typed"]
        sections = {
            "Definition": s["Definition"],
            "Body":       s["Body"],
            "Conclusion": s["Conclusion"],
        }

        if typed:
            fname    = f"student_{sid}_{label}.pdf"
            out_path = os.path.join(TYPED_DIR, fname)
            make_typed_pdf(out_path, sections)
            print(f"  [T] {fname}")
            typed_count += 1
        else:
            noise    = s.get("noise", "medium")
            fname    = f"student_{sid}_{label}.pdf"
            out_path = os.path.join(SCANNED_DIR, fname)
            make_scanned_pdf(out_path, sections, noise_level=noise)
            print(f"  [S] {fname}  (noise={noise})")
            scanned_count += 1

    print()
    print(f"[DONE] Generated: {typed_count} typed + {scanned_count} scanned = "
          f"{typed_count + scanned_count} student PDFs")
    print(f"       Output directory: {OUT_DIR}")
    print()
    print("Next step: python run_realworld_test.py")


if __name__ == "__main__":
    main()
