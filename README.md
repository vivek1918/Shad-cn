# MeltMagic Internship Assessment

## 🧠 Project: Fine-Tune LLaMA 3.1 to Generate ShadCN UI Components

This repository contains the solution to the MeltMagic Summer Internship assignment. The goal is to fine-tune the **LLaMA 3.1 8B** model to generate **ShadCN-style UI components** and output them in a structured JSON schema.

---

## 📌 Objective

Fine-tune an open-source LLaMA 3.1 model to generate valid ShadCN-style components as JSON registry items.

### 🔧 Example Output
```json
{
  "$schema": "https://ui.shadcn.com/schema/registry-item.json",
  "name": "marquee",
  "type": "registry:ui",
  ...
}
