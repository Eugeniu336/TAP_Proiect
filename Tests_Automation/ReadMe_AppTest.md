# TestApp – Modular Plugin-Based AI Processing System

This project implements a **server–client system with dynamic plugin loading**, allowing
different types of data processing depending on which plugins (clients) are connected.
The application includes:

- A **central server** (Python + PyQt5 GUI)
- Multiple **client modules** (plugins) that perform tasks such as:
  - CSV preprocessing
  - Model training (Model1, Model2)
  - Validation
  - Prediction
- A complete **automated testing framework** with 3 levels of test suites:
  - Technical (unit + integration)
  - Functional (workflow + GUI interactions)
  - Advanced (server concurrency + load + stress)

The goal is to ensure that the entire system behaves correctly under different configurations
and that the server can dynamically build final AI models based on available plugins.

---

## 📂 Project Structure

