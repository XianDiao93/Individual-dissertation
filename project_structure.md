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
|  |  |  |- email_router.py
|  |  |  |- group_router.py
|  |  |  |- auth_router.py
|  |  |  |- profile_router.py
|  |  |
|  |  |- services/
|  |  |  |- __init__.py
|  |  |  |- llm_client.py
|  |  |  |- extraction.py
|  |  |  |- product.py
|  |  |  |- political_geopolitical.py
|  |  |  |- business_environment.py
|  |  |  |- transaction_fraud.py
|  |  |  |- intent_conversation.py
|  |  |  |- regulatory_legal_risk.py
|  |  |  |- cultural_communication_risk.py
|  |  |  |- risk.py
|  |  |  |- decision_engine.py
|  |  |  |- communication.py
|  |  |  |- document.py
|  |  |  |- logging_service.py
|  |  |  |- email.py
|  |  |  |- group.py
|  |  |  |- profile.py
|  |  |  |- auth.py
|  |  |  |- user_data_store.py
|  |  |  |- id_service.py
|  |  |  |- email_enrichment.py
|  |  |
|  |  |- models/
|  |  |  |- __init__.py
|  |  |  |- trade_case_model.py
|  |  |  |- com_model.py
|  |  |  |- doc_model.py
|  |  |  |- risk_model.py
|  |  |  |- sanctions_model.py
|  |  |  |- auth_model.py
|  |  |  |- email_model.py
|  |  |  |- group_model.py
|  |  |  |- profile_model.py
|  |  |  |- common_model.py
|  |  |
|  |  |- database/                     #The data from open source database
|  |  |  |- system_prompts/
|  |  |  |  |- chat_basic.json
|  |  |  |  |- doc_basic.json
|  |  |  |  |- extraction_basic.json
|  |  |  |- regions/
|  |  |  |  |- country_codes.json
|  |  |  |- risks/
|  |  |     |- risk_categories.json
|  |  |     |- business_environment/
|  |  |     |  |- data source.md
|  |  |     |  |- country_tags.json
|  |  |     |  |- tags.json
|  |  |     |- cultural_communication/
|  |  |     |  |- tags.json
|  |  |     |- intent_conversation/
|  |  |     |  |- tags.json
|  |  |     |- political_geopolitical/
|  |  |     |  |- data source.md
|  |  |     |  |- country_tags.json
|  |  |     |  |- tags.json
|  |  |     |- product/
|  |  |     |  |- product_keywords.json
|  |  |     |  |- tags.json
|  |  |     |- regulatory_legal/
|  |  |     |  |- tags.json
|  |  |     |- transaction_fraud/
|  |  |        |- tags.json
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
|  |     |- InputPanel.js
|  |     |- OutputPanel.js
|  |     |- RiskBanner.js
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
|     |- final_presentation.pptx
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
|  |  |  |- documents
|  |  |  |- emails/
|  |  |  |  |- em_00001.json
|  |  |  |  |- em_00002.json
|  |  |  |- profile.json
|  |  |- 0002/
|  |     |- documents
|  |     |- emails/
|  |     |  |- em_00001.json
|  |     |  |- em_00002.json
|  |     |- profile.json
|  |- surveys/                   # 问卷与回答（你最需要）
|  |  |- survey_schema.json
|  |  |- responses/
|  |     |- 0001_response.json
|  |- logs/                      # 用户操作日志（用于评估）
|     |- 0001_cases.json
|
|- .gitignore
|- README.md
|- project_config_example.json
|- project_structure.md     // this file