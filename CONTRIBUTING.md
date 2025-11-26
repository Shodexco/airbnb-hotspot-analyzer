# Contributing Guide

Thank you for considering contributing to the Airbnb Hotspot Analyzer!

---

# 🧱 Project Structure (Important)

Core analysis logic:
```
airbnb_analyzer.py
```

API + UI server:
```
api_server.py
```

Frontend (dashboard, hotspots, maps):
```
templates/
static/
```

Generated content (ignored by git):
```
maps/
output/
```

---

# 🧑‍💻 How to Contribute

### 1. Fork the repo  
### 2. Create a feature branch  
```
git checkout -b feature/my-new-feature
```

### 3. Make your changes  
- Add new cities  
- Add new score metrics  
- Improve clustering logic  
- Fix bugs  
- Improve frontend UI  

### 4. Format your code  
Stick to Black/PEP8 style.

### 5. Submit a Pull Request  
Include:
- Description of change  
- Screenshots (if UI changes)  
- Example API output (if backend changes)

---

# 🧪 Testing Your Changes

```
python api_server.py
```

Use:
- `/api-tester`  
- `/hotspots`
- `/maps`

---

# 🧹 Git Hygiene

- Don’t commit generated map HTML  
- Don’t commit large CSVs  
- Don’t commit secrets

---

# 🙏 Thanks
Every contribution makes this project stronger.
