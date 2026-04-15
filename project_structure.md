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
|  |  |- database/
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
|  |     |- llm_doc_utils.py
|  |     |- llm_reply_utils.py
|  |
|  |- tests/
|  |  |- test_communication.py
|  |  |- test_decision_engine.py
|  |  |- test_extraction.py
|  |  |- test_llm_client.py
|  |  |- test_risks.py
|  |
|  |- requirements.txt
|  |- README.md
|
|- frontend/
|  |- src/
|  |  |- index.html
|  |  |- main.js
|  |  |- api.js
|  |  |- styles.css
|  |
|  |- public
|  |- README.md
|
|- data/
|  |- raw/
|  |  |- business_emails/
|  |  |- business_text/
|  |  |- contract_templates/
|  |  |- multilingual/
|  |  |- multilingual_tone/
|  |  |- user_manual_templates/
|  |- processed/
|  |  |- dataset.json
|  |- documents_templates/
|  |- survey/
|  |  |- example_input_and_expected_output/
|  |     |- block_cases.json
|  |     |- localization_cases.json
|  |     |- normal_cases.json
|  |     |- warn_cases.json
|  |- README.md
|
|- docs/
|  |- proposal/
|  |  |- 20513832_Xian_Diao_Proposal.pdf
|  |- report/
|  |  |- interim_report.pdf
|  |  |- final_report.pdf
|  |- ethic_related/
|  |  |- 20513832_Xian_Diao_CS_REC_2 SOP2.2_Text_Data.pdf
|  |  |- 20513832_Xian_Diao_Data_Management_Plan.pdf
|  |- slides/
|     |- final_presentation.pptx
|
|- output/
|  |- documents/
|     |- sales_contract_20251130_180806.pdf
|     |- sales_contract_20260309_094043.pdf
|
|- user_data/
|  |- users.json
|  |- user_data/
|  |  |- 0001/
|  |  |  |- documents/
|  |  |  |- emails/
|  |  |  |  |- em_00001.json
|  |  |  |  |- em_00002.json
|  |  |  |  |- ...
|  |  |  |- profile.json
|  |  |- 0002/
|  |     |- documents/
|  |     |- emails/
|  |     |  |- em_00001.json
|  |     |  |- em_00002.json
|  |  |  |  |- ...
|  |     |- profile.json
|  |  |- 0003/
|  |     |- documents/
|  |     |- emails/
|  |     |  |- em_00001.json
|  |     |  |- em_00002.json
|  |  |  |  |- ...
|  |     |- profile.json
|  |- logs/
|
|- .gitignore
|- README.md
|- project_structure.md     // this file