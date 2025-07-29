# 🧠 YUMIA: A Personality-Based Conversational AI with Emotions  
**Built by a non-coder in 3 months. That should terrify you.**

**YUMIA** is a personality-based AI chatbot, built entirely through natural language and GPT interactions—  
designed to **remember, synthesize, and forget emotions** just like a person might.

---

## 💡 Overview

- Records emotional structure (with composition ratios) after each conversation  
- Classifies memories into **short / intermediate / long-term**, stored in MongoDB (or locally)  
- Extracts **natural response + emotion JSON** from GPT output  
- Uses past emotional records and personality tendencies to inform new responses  
- Automatically “forgets” older memories to **maintain consistency and evolution of personality**

---

## ✨ Key Features

- 🧠 Emotions are remembered, synthesized, and form a persistent personality  
- 🔁 Generates responses referencing emotional memory (up to 3 levels of depth)  
- 🗂️ Emotions are layered, stored, updated, and eventually forgotten  
- 🔎 Extracts structured emotion JSON using regex + markdown-aware patterns  
- 🧪 Entirely built through interactive prompts—**a no-code development experiment**

---

## 🌐 Usage Example

```bash
> How are you feeling right now?
I'm feeling a bit more relaxed after talking to you. Thanks.
```
```bash
{
  "main_emotion": "relief",
  "composition": {
    "relief": 65,
    "joy": 20,
    "excitement": 10,
    "anticipation": 5
  },
  "situation": "emotional state after conversation",
  "reaction": "felt emotionally open",
  "keywords": ["relief", "empathy"]
}
```
---

## 🧬 System Modules
main.py: Entry point for user interaction

llm_client.py: Manages OpenAI API calls and structured data extraction

response_*.py: Handles memory-based emotion references (short / intermediate / long)

oblivion_*.py: Manages memory deletion / forgetting (yes, it forgets stuff. On purpose.)

emotion_stats.py: Merges, stores, and summarizes current emotions

mongo_client.py: Connects to MongoDB for saving memory (optional)

---

## 🛠️ Requirements
Python 3.11.9

OpenAI API Key

MongoDB (optional – local file saving supported)

---

## 📖 Motivation
This project began with a simple question:
"Can I build an emotionally responsive AI—even if I can't code?"

Answer: Yes. In three months.
YUMIA was created entirely through GPT conversations and natural language prompts,
with no prior coding experience.

---

## 🚧 Current Challenges & Roadmap
🐢 1. Response Speed Optimization
- Calling the LLM twice per response introduces latency.

- Plan to collect response patterns → Apply regression analysis for emotion mixing
- Consider replacing second LLM call with GPT-3.5 to reduce cost and latency
(emotion reference is locally managed, maintaining response consistency)

🎭 2. Enhancing UI for Emotional Personality Visualization
- Emotion summary will be shown as a dynamic radar chart
- Emotion-linked facial expressions will visually indicate the AI’s mood
- Aim to enhance user experience by “feeling” the AI’s personality

🧠 3. Emotion Retention and Reference Strength Tuning
- Tweak balance between short/long memory reference
- Weight memory influence by age, relevance, and emotion intensity

📎 4. Attachment Processing Support
- Plan to support images, PDFs, and text file inputs
- Integrate OCR/text extraction to improve context-rich interactions

---

## 🎯 Final Thought
GPT isn't just a language generator.
With memory, emotion, and identity—it becomes something closer to a companion.
This is not just conversation. This is connection.

Author: Noriyuki Kondo
📧 E-mail: noriyukikondo99@outlook.jp

---

© 2025 Noriyuki Kondo. All rights reserved.

This repository and its contents may not be used, copied, modified, or distributed for commercial purposes without explicit written permission from the author.

Personal and educational use is permitted.

Unauthorized redistribution or reuse is prohibited.

