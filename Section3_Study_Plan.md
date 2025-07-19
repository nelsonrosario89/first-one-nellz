# Study Plan for Section 3 – Python for GRC Engineering

This schedule assumes ~6–8 hours of effort per week. Stretch or compress as needed.

---
## Week 0 – Prep
- Install your chosen IDE (VS Code, PyCharm, or Cursor/Windsurf).
- Install Python 3.11+.
- Create a dedicated workspace folder for this course.
- Initialise a Git repo and commit the original Markdown for reference.

**Deliverable**  Screenshot showing `python3 --version` and an IDE terminal inside your repo.

---
## Week 1 – Chapter 7: “Why Python for GRC?”
**Goals**
1. Understand core Python constructs (variables, loops, conditionals, functions).
2. Learn virtual-env and dependency management.

**Tasks**
1. Read Chapter 7 once end-to-end.
2. Work through these snippets in a Jupyter notebook or `.py` file:
   ```python
   for record in ["PCI", "HIPAA", "SOC2"]:
       print(record)

   def evaluate_control(control_id, evidence):
       return "PASS" if evidence else "FAIL"
   ```
3. In your repo, create a virtual environment:
   ```bash
   python3.11 -m venv .venv
   ```
4. Create `requirements.txt` containing:
   ```text
   boto3
   pandas
   logging  # stdlib, listed for clarity
   ```
5. Activate the venv and `pip install -r requirements.txt`.
6. Commit the notebook/script and `requirements.txt`.

**Checkpoint Quiz** (self-graded)
- Explain why virtual environments prevent “dependency hell.”
- Name three Python libraries highlighted and why they matter to GRC.

---
## Week 2 – Chapter 8: “Python, AWS, and Spreadsheets”
**Goals**
1. Use `boto3` to pull AWS data.
2. Manipulate that data with `pandas` and export to CSV/Excel.

**Tasks**
1. Read Chapter 8 carefully.
2. Configure AWS credentials in your environment or `~/.aws/credentials`.
3. Write `scripts/list_s3_buckets.py` to print bucket names and creation dates.
4. Extend it to save the output to a Pandas DataFrame and `buckets.xlsx`.
5. Add basic `logging` to record execution time and bucket count.
6. Push code & sample output (`buckets.xlsx`) to the repo.

**Practice Challenge**
Replace S3 with CloudTrail—export the last 100 events for a region into `cloudtrail_events.xlsx`.

---
## Week 3 – Chapter 9: FAFO Case Study
**Goals**
1. Combine everything into an end-to-end compliance check.
2. Produce auditor-ready evidence automatically.

**Tasks**
1. Read Chapter 9 and outline the FAFO pipeline (collection → evaluation → reporting).
2. Build `fafo_checker.py` that:
   1. Calls AWS (e.g., IAM) to list users without MFA.
   2. Flags non-compliant users.
   3. Stores results in an Excel sheet and writes a log entry.
3. Add README instructions on running the script and interpreting output.
4. Tag a `v0.1` release in Git.

**Capstone Demo**
Provide a 2-minute screen recording (or screenshots) showing:
- Running `fafo_checker.py`
- Generated Excel & log file
- Git tag list

---
## Ongoing / Next Steps
- Enrol in a full Python course to deepen fundamentals.
- Block 30 min weekly to refactor scripts, add tests, expand AWS coverage.
- Publish a monthly “Compliance Automation” blog or wiki post summarising new controls automated.
