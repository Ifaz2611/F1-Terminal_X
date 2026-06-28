## 🏁 F1 Telemetry PR Template

### **Describe the changes**
Brief summary of what this PR introduces (feature, bug fix, optimization, docs, etc.)

### **Type of change**
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] 🚀 Performance improvement
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration / dependencies
- [ ] ♻️ Refactoring (no logic changes)
- [ ] 🧪 Tests / CI improvements
- [ ] ⚠️ Breaking change

### **Related Issues**
Closes #(issue number) or References #(issue number)

### **Changes Made**
- List key changes/additions
- Include file names or modules modified
- Highlight any new functions or classes introduced

### **Testing**
- [ ] Unit tests added/updated
- [ ] Integration tests passing
- [ ] Tested locally with sample data
- [ ] Verified with FastF1 API (if applicable)

**Test coverage:**
- Data sources tested: (e.g., FastF1, CSV, Parquet)
- Drivers/sessions tested: (e.g., VER, HAM; 2023 Monza Q)
- Edge cases verified: (e.g., missing data, single lap, etc.)

### **Data Validation**
If this affects data loading, transformation, or ML features:
- [ ] Verified output shape and dtypes
- [ ] Checked for NaN/null handling
- [ ] Confirmed backward compatibility with existing CSVs
- [ ] Sample telemetry processed successfully

### **Performance Impact**
If applicable:
- Execution time: before → after
- Memory usage: before → after
- Benchmark dataset: (e.g., full 2023 season, single session)

### **Dependencies**
- [ ] No new dependencies added
- [ ] Dependencies updated in `requirements.txt`
- [ ] Version constraints documented

### **Breaking Changes**
- [ ] No breaking changes
- [ ] Migration guide provided (if breaking)
- [ ] Deprecation warnings added (if applicable)

### **Documentation**
- [ ] Updated README if feature-level changes
- [ ] Added docstrings (NumPy/SciPy style)
- [ ] Updated inline comments where logic is non-obvious
- [ ] Examples provided (if new public API)

### **Checklist**
- [ ] Code follows project style (PEP 8, type hints where applicable)
- [ ] No unused imports or dead code
- [ ] Commit messages are clear and descriptive
- [ ] All tests pass locally (`pytest`)
- [ ] This PR is ready for review

### **Screenshots / Output** (if applicable)
*Paste plots, tables, or dashboard previews here*

---

**Thank you for contributing to F1 Terminal_X! 🏎️**
