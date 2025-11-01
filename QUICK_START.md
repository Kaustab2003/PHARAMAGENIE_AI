# 🚀 PharmaGenie AI - Quick Start Guide

## 📦 Installation (5 minutes)

### Step 1: Install Python
Make sure you have Python 3.9 or higher installed:
```bash
python --version
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 🎯 Quick Feature Tour

### 1. Drug Explorer (NEW! 💊)
**What it does**: Get comprehensive drug information including class, mechanism, interactions, and molecular structure

**How to use**:
1. Click "Drug Explorer" in the sidebar
2. Enter a drug name (e.g., "Aspirin")
3. Click "Search Drug"
4. Explore 5 tabs of information

**Example drugs to try**:
- Aspirin
- Ibuprofen
- Metformin
- Omeprazole
- Amoxicillin

---

### 2. Molecule Visualizer (🔬)
**What it does**: Visualize drug molecules in 2D and 3D

**How to use**:
1. Click "Molecule Visualizer"
2. Enter drug name or SMILES string
3. View 2D structure and interactive 3D model
4. Download structure as SDF file

**Try these**:
- Caffeine
- Paracetamol
- Atorvastatin

---

### 3. Drug Repurposing Analysis (🔄)
**What it does**: Comprehensive analysis for drug repurposing opportunities

**How to use**:
1. Go to "Analysis" page
2. Enter drug name
3. Optional: Add therapeutic area
4. Click "Start Analysis"
5. View report with:
   - Market analysis
   - Patent landscape
   - Clinical trials
   - Web intelligence

---

## 📊 What Information You Get

### Drug Explorer Provides:
| Category | Information |
|----------|-------------|
| **Classification** | Therapeutic class (e.g., Analgesic, NSAID) |
| **Mechanism** | How the drug works pharmacologically |
| **Uses** | FDA-approved indications and descriptions |
| **Adverse Effects** | Common and serious side effects |
| **Drug Interactions** | Interactions with other medications |
| **Food Interactions** | What to avoid while taking the drug |
| **Molecular Info** | Formula, weight, IUPAC name |
| **3D Structure** | Interactive molecular model |

---

## 🔍 Example Workflow

### Scenario: Researching Aspirin

1. **Start with Drug Explorer**
   - Enter "Aspirin"
   - Learn it's an NSAID analgesic
   - See mechanism: COX enzyme inhibition
   - Check interactions (e.g., Warfarin)

2. **Visualize the Molecule**
   - Go to Molecule Visualizer
   - Enter "Aspirin"
   - Rotate 3D model
   - See molecular weight: 180.16 g/mol

3. **Analyze for Repurposing**
   - Go to Analysis page
   - Enter "Aspirin" + "Oncology"
   - Get market data and clinical trials
   - Review patent landscape

4. **Export Results**
   - Download PDF report
   - Email to team
   - Save for later reference

---

## 💡 Pro Tips

### Getting Better Results
1. **Use generic names**: "Ibuprofen" not "Advil"
2. **Check synonyms**: Drug Explorer shows alternative names
3. **Try SMILES**: For exact molecular matches
4. **Use examples**: Click example buttons for quick tests

### Troubleshooting
- **Drug not found**: Check spelling or try synonym
- **Slow loading**: First search takes longer (caching)
- **No 3D model**: Some molecules may not render
- **API errors**: Wait a moment and retry

---

## 🆓 Free APIs Used

All features use **100% FREE** APIs:

| API | Purpose | Limit |
|-----|---------|-------|
| **RxNav** | Drug info & interactions | Unlimited |
| **PubChem** | Molecular data | 5 req/sec |
| **PubMed** | Research articles | 3 req/sec |
| **World Bank** | Trade data | Generous |

**No API keys required for basic features!**

---

## 🎓 Learning Resources

### Understanding Drug Information
- **Drug Class**: Therapeutic category (e.g., antibiotics, analgesics)
- **Mechanism of Action**: How the drug produces its effect
- **RxCUI**: Unique identifier in RxNorm database
- **SMILES**: Text representation of molecular structure
- **LogP**: Measure of lipophilicity (fat solubility)

### Molecular Properties
- **Molecular Weight**: Mass of one molecule (g/mol)
- **H-Bond Donors**: Hydrogen bond donors (affects absorption)
- **H-Bond Acceptors**: Hydrogen bond acceptors
- **Rotatable Bonds**: Flexibility of molecule

---

## 🔐 Privacy & Safety

✅ **What we DON'T collect**:
- Personal information
- Search history
- User accounts
- Payment information

✅ **What we DO**:
- Cache API responses temporarily
- Log errors for debugging
- Provide anonymous usage statistics

⚠️ **Important**: This tool is for educational purposes. Always consult healthcare professionals for medical advice.

---

## 🐛 Common Issues & Solutions

### Issue: "Drug not found"
**Solution**: 
- Check spelling
- Try generic name instead of brand name
- Use Drug Explorer's synonym list

### Issue: "API timeout"
**Solution**:
- Check internet connection
- Wait 30 seconds and retry
- Try a different drug

### Issue: "No 3D structure available"
**Solution**:
- Some molecules are too complex
- Try 2D structure instead
- Check if SMILES string is valid

### Issue: "Slow performance"
**Solution**:
- First search is slower (caching)
- Close other browser tabs
- Clear browser cache

---

## 📞 Need Help?

- **Documentation**: See `PROJECT_OVERVIEW.md`
- **Issues**: Report on GitHub
- **Questions**: Check FAQ section
- **Updates**: Follow changelog

---

## 🎉 Next Steps

1. ✅ Try the Drug Explorer with your favorite drug
2. ✅ Visualize a molecule in 3D
3. ✅ Run a complete drug analysis
4. ✅ Export a report
5. ✅ Explore batch processing

**Happy exploring! 💊🔬**

---

**Quick Start Guide v2.0** | Last Updated: October 2025
