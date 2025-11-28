Individual dissertation/
|- backend/                     # backend (Python + FastAPI/Flask)
|  |- run_backend.py            # launcher of backend
|  |- app/
|  |  |- __init__.py
|  |  |- main.py                # 主入口：启动 API 的文件
|  |  |- config.py              # 配置（比如数据路径、API key 读取）
|  |  |- routers/               # 各种接口路由（按功能拆分）
|  |  |  |- __init__.py
|  |  |  |- com_router.py             # 聊天/邮件生成接口
|  |  |  |- doc_router_.py         # 文档生成接口
|  |  |  |- risk_router.py             # 风险识别接口
|  |  |- services/              # 业务逻辑层（调用 LLM、组合结果）
|  |  |  |- __init__.py
|  |  |  |- llm_client.py       # 封装 OpenAI/其他 LLM 调用
|  |  |  |- communication.py    # 智能沟通逻辑
|  |  |  |- document.py    # 贸易文档生成逻辑
|  |  |  |- risk.py    # 风险识别逻辑
|  |  |- models/                # Pydantic 数据模型
|  |  |  |- __init__.py
|  |  |  |- com_model.py
|  |  |  |- doc_model.py
|  |  |  |- risk_model.py
|  |  |- utils/                 # 工具函数
|  |     |- __init__.py
|  |     |- file_utils.py       # 读取数据、保存结果等
|  |- tests/                    # 后端单元测试（可选）
|  |- requirements.txt          # Python 依赖
|  |- README.md
|
|- frontend/                    # 前端（网页界面）
|  |- public/                   # 静态资源（图标、logo 等）
|  |- src/
|  |  |- index.html             # 单页应用入口（若用纯 HTML）
|  |  |- main.js                # 前端主逻辑，调用后端 API
|  |  |- api.js                 # 封装调用 /api/chat 等接口
|  |  |- styles.css             # 样式
|  |  |- components/            # 如果用 React，可以放组件
|  |- package.json              # 如果用 npm / React，这里会有
|  |- README.md
|
|- data/                        # 所有“训练/评测/样例数据”都放这里 ✅
|  |- raw/                      # 原始数据（公开模板、原始文本等）
|  |- processed/                # 清洗后的 JSON、CSV、可直接使用的数据
|  |  |- dataset.json           # 你之前设计的统一 JSON 格式数据
|  |- prompts/                  # prompt 设计、few-shot 示例
|  |  |- communication_examples.json
|  |  |- document_examples.json
|  |  |- risk_examples.json
|  |- documents_templates/      # templates of PI, Invoice files(docx, jinja2)
|  |  |- pi_template.docx
|  |  |- invoice_template.docx
|  |- README.md
|
|- experiments/                 # 实验与评估（方便写论文结果）
|  |- notebooks/                # Analysis with Jupyter Notebook
|  |  |- prompt_ablation.ipynb  # 不同 prompt 对比实验
|  |  |- eval_results.ipynb     # 评测结果分析
|  |- logs/                     # 运行日志、实验记录
|  |- results/                  # 评测输出、对比结果 JSON/CSV
|
|- docs/                        # 文档类内容（写给人看的）
|  |- proposal/                 # 提案相关
|  |  |- 20513832_Xian_Diao_Proposal.pdf
|  |- literature/               # 文献整理、笔记
|  |  |- reading_notes.md
|  |  |- references.bib
|  |- report/                   # 最终论文/中期报告草稿
|  |  |- interim_report.docx
|  |  |- dissertation_draft.docx
|  |  |- figures/               # 论文里的图表
|  |- slides/                   # 答辩 PPT
|     |- final_presentation.pptx
|
|- models/                      # （可选）微调模型 / 本地模型等
|  |- finetuned/                # 微调后的模型信息、配置
|  |- README.md
|
|- .gitignore                   # gitignore file
|- README.md                    # 整个项目的说明（项目介绍、如何运行）
|- project_config_example.json  # 配置模板（例如 API key 填在本地 config 里）
|- project_structure            # This file
