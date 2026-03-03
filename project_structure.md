Overall System Architecture:
User Input
   ↓
Trade Facts Extraction
   ↓
Review Layer (Sanctions & Risk Screening)
   ↓
Decision Routing (BLOCK / WARN / CLEAR)
   ↓
Communication or Document Generation
   ↓
UI Presentation + Risk Annotation
   ↓
Logging & Evaluation Storage


Individual dissertation/
|
|- backend/
|  |- run_backend.py
|  |- app/
|  |  |- __init__.py
|  |  |- main.py
|  |  |- config.py
|  |  |- routers/
|  |  |  |- __init__.py
|  |  |  |- com_router.py
|  |  |  |- doc_router.py
|  |  |  |- risk_router.py
|  |  |  |- screening_router.py
|  |  |  |- auth_router.py
|  |  |
|  |  |- services/
|  |  |  |- __init__.py
|  |  |  |- llm_client.py
|  |  |  |- extraction.py
|  |  |  |- sanctions.py
|  |  |  |- risk.py
|  |  |  |- decision_engine.py
|  |  |  |- communication.py
|  |  |  |- document.py
|  |  |  |- logging_service.py
|  |  |  |- auth.py
|  |  |
|  |  |- models/
|  |  |  |- __init__.py
|  |  |  |- trade_case_model.py
|  |  |  |- com_model.py
|  |  |  |- doc_model.py
|  |  |  |- risk_model.py
|  |  |  |- sanctions_model.py
|  |  |  |- auth_model.py
|  |  |
|  |  |- database/                     #The data from open source database
|  |  |  |- sanctions_rules.json
|  |  |  |- country_risk_tiers.json
|  |  |  |- sample_trade_cases.json
|  |  |
|  |  |- utils/
|  |     |- __init__.py
|  |     |- file_utils.py
|  |
|  |- tests/
|  |- requirements.txt
|  |- README.md
|
|- frontend/
|  |- public/
|  |- src/
|  |  |- index.html
|  |  |- main.js
|  |  |- api.js
|  |  |- styles.css
|  |  |- components/
|  |  |  |- InputPanel.js
|  |  |  |- OutputPanel.js
|  |  |  |- RiskBanner.js
|  |
|  |- package.json
|  |- README.md
|
|- data/
|  |- raw/
|  |- processed/
|  |  |- dataset.json
|  |- prompts/
|  |  |- communication_examples.json
|  |  |- document_examples.json
|  |  |- risk_examples.json
|  |- documents_templates/
|  |  |- pi_template.docx
|  |  |- invoice_template.docx
|  |- README.md
|
|- experiments/
|  |- notebooks/
|  |  |- screening_eval.ipynb
|  |  |- prompt_ablation.ipynb
|  |  |- user_study_analysis.ipynb
|  |- logs/
|  |- results/
|
|- docs/
|  |- proposal/
|  |  |- 20513832_Xian_Diao_Proposal.pdf
|  |- literature/
|  |  |- reading_notes.md
|  |  |- references.bib
|  |- report/
|  |  |- interim_report.docx
|  |  |- dissertation_draft.docx
|  |  |- figures/
|  |- slides/
|    |- final_presentation.pptx
|
|- models/
|  |- finetuned/
|  |- README.md
|
|- output/
|
|- user_data/
|  |- users.json                 # 模拟账号列表（登录用）
|  |- user_data/                  # 每个用户的业务画像/偏好
|  |  |- 0001/
|  |    |- customers/
|  |    |- documents
|  |    |- emails/
|  |    |- replies/
|  |    |- 0001_profile.json
|  |- surveys/                   # 问卷与回答（你最需要）
|  |  |- survey_schema.json
|  |  |- responses/
|  |     |- 0001_response.json
|  |- logs/                      # 用户操作日志（用于评估）
|     |- 0001_cases.jsonl
|
|- .gitignore
|- README.md
|- project_config_example.json
|- project_structure.md     // this file