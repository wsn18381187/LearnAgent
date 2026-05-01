# LearnAgent

> 一个基于 OpenAI SDK 的智能 Agent 框架，具备双重记忆系统与 Condition Flow 复杂任务处理引擎。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Developing-orange.svg)](https://github.com/wsn18381187/LearnAgent)

---

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                     main.py                          │
│               (入口 & 对话循环)                        │
└──────────┬────────────────────────────┬──────────────┘
           │                            │
    简单任务                            复杂任务
           │                            │
           ▼                            ▼
┌──────────────────┐    ┌──────────────────────────────┐
│  judge_which_model │    │     Condition Flow 引擎       │
│  (强弱模型自动切换)  │    │  Plan → Execute → Judge →    │
│  + 工具调用        │    │  Conclude (循环至满足条件)     │
└──────┬───────────┘    └──────────────┬───────────────┘
       │                               │
       └───────────┬───────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│                   双重记忆系统                         │
│  ┌──────────────┐        ┌──────────────────────┐   │
│  │  用户画像      │        │  ChromaDB RAG 向量库  │   │
│  │  (一级记忆)    │        │  (二级记忆)           │   │
│  │  偏好/事实/    │        │  历史对话嵌入 & 检索   │   │
│  │  最近对话总结  │        │  滑动窗口自动更新      │   │
│  └──────────────┘        └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 核心特性

### 🔄 Condition Flow — 复杂任务处理引擎

针对需要多步推理的复杂任务，Condition Flow 采用 **Plan → Execute → Judge → Conclude** 循环架构：

1. **Plan（规划）**：分析任务背景与目标，拆分为多个子任务
2. **Execute（执行）**：顺序执行每个子任务，仅传递执行结果而非完整过程
3. **Judge（判断）**：评估当前结果是否满足预期，决定继续或退出
4. **Conclude（总结）**：汇总所有步骤结果，输出最终报告

> 相比直接多步推理，Condition Flow 在保留关键信息的同时避免上下文膨胀，适合复杂任务场景。

### 🧠 双重记忆系统

| 层级 | 实现 | 功能 |
|------|------|------|
| 一级记忆 | 用户画像 (`user_image.json`) | 记录用户基本信息、偏好、事实、最近对话总结 |
| 二级记忆 | ChromaDB RAG 向量库 | 历史对话嵌入存储，按需检索相关内容 |

- 每次对话结束后自动更新用户画像
- 滑动窗口机制将对话片段嵌入 ChromaDB，实现长期记忆检索

### 🛠 CodeAct 模式

文件写入统一走 CodeAct 模式：LLM 生成 Python 代码直接执行文件写入，彻底规避 JSON function call 中的字符转义问题。

### ⚡ 自动强弱模型切换

根据任务复杂度自动选择合适的模型：
- **简单任务** → 弱模型（快速响应，节省成本）
- **复杂任务** → 强模型（深度推理）

### 🔧 内置工具集

| 工具 | 功能 |
|------|------|
| `search_web` | 联网搜索（Tavily API） |
| `read_file` | 读取本地文件 |
| `write_file` | CodeAct 模式写入文件 |
| `execute_terminal_command` | 执行终端命令 |
| `rag_history_search` | 检索历史对话 |
| `get_current_time` | 获取当前时间 |
| `ask_user_more_info` | 向用户追问 |

---

## 项目结构

```
LearnAgent/
├── LearnAgent.md              # 详细设计文档
├── README.md                  # 本文件
├── requirement.txt            # Python 依赖
├── .gitignore                 # Git 忽略规则
├── chromadbtest/              # ChromaDB 集成测试
│   └── chromadbtest.py
└── code-v0_1/                 # 核心代码
    ├── main.py                # 入口 & 对话循环
    ├── .env                   # API 密钥（不纳入版本控制）
    ├── core/                  # 核心引擎
    │   ├── condition_flow.py           # Condition Flow 主循环
    │   ├── condition_flow_definiton.py # Flow 各阶段 Prompt 定义
    │   ├── flow_entrance.py            # Flow 入口 & 工具解析
    │   ├── flow_functions.py           # Plan/Execute/Judge/Conclude 实现
    │   └── code_act_executor.py        # CodeAct 代码执行器
    ├── functions/             # 功能模块
    │   ├── judge_which_model.py        # 强弱模型路由
    │   ├── get_model_response.py       # 模型调用封装
    │   ├── use_tools_to_analyze.py     # 工具调用解析
    │   ├── choose_which_tools.py       # 工具注册 & 选择
    │   ├── auto_configuration.py       # 模型配置
    │   ├── user_image.py               # 用户画像管理
    │   ├── rag_by_chromadb.py          # RAG 检索
    │   ├── auto_history_embedding.py   # 历史对话自动嵌入
    │   └── get_embedding.py            # Embedding 模型
    ├── tools/                 # 工具实现
    │   ├── search_web.py
    │   ├── read_file.py
    │   ├── write_file.py
    │   ├── terminal_command.py
    │   ├── rag_history_search.py
    │   ├── get_current_time.py
    │   └── ask_user_more_info.py
    ├── history/               # 对话历史（不纳入版本控制）
    ├── log/                   # 请求日志（不纳入版本控制）
    ├── chromaDB/              # 向量数据库（不纳入版本控制）
    └── user_info/             # 用户画像数据（不纳入版本控制）
```

---

## 快速启动

### 1. 环境配置

```bash
conda create -n la python==3.10
conda activate la
pip install openai python-dotenv chromadb
```

### 2. API 配置

在 `code-v0_1/` 目录下创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
TAVILY_API_KEY=your_tavily_key_here
```

在 `functions/auto_configuration.py` 中配置模型 Base URL、模型名称等参数，支持强弱模型搭配。

在 `functions/get_embedding.py` 中配置 Embedding 模型（确定后不要更改，否则向量库需重建）。

### 3. 用户画像初始化

在 `code-v0_1/` 下创建 `user_info/user_image.json`：

```json
{
  "basic_info": {},
  "preferences": [],
  "facts": [],
  "chat_history": [],
  "last_interaction": ""
}
```

### 4. 启动

```bash
cd code-v0_1
python main.py
```

---

## 技术栈

- **语言**：Python 3.10+
- **模型调用**：OpenAI SDK（兼容 DeepSeek、OpenRouter 等）
- **向量数据库**：ChromaDB
- **搜索**：Tavily Search API
- **依赖**：`openai`, `python-dotenv`, `chromadb`

---

## 开发日志

<details>
<summary><b>4.27 — 双重记忆系统</b></summary>

- 扩展用户画像功能，新增最近对话内容记录，构成一级记忆
- 基于 ChromaDB 构建 RAG 向量库，实现二级记忆系统
- 封装 RAG 检索 Tool 和滑动窗口自动嵌入机制
- 实现既能快速响应最近事件，又能动态检索历史信息

</details>

<details>
<summary><b>4.28 — 模型切换 & 文件工具</b></summary>

- 基座模型切换为 DeepSeek V4（Flash + Pro），处理 reasoning 兼容性
- 添加文件读取工具，支持常见代码和标记格式
- 构思 Agent 核心状态机：任务分析 → 分步规划 → 执行子任务 → 汇总验收

</details>

<details>
<summary><b>4.30 — Condition Flow 设计</b></summary>

- 设计并实现 Condition Flow 核心功能
- Plan → Execute → Judge → Conclude 循环架构
- 每步仅传递执行结果，避免上下文膨胀

</details>

<details>
<summary><b>5.1 — 稳定性 & CodeAct</b></summary>

- 修复大量模型返回异常 bug，增加容错机制（JSON 解析失败重试、连续失败计数等）
- 实现 CodeAct 模式：文件写入统一走 Python 代码执行，彻底规避 JSON 转义问题
- 修复 flow_entrance 参数名遮蔽、parse_json_list 异常未捕获等多个严重 bug
- Condition Flow 成功通过武汉天气分析、日元上涨分析、科技公司产品页面生成等多项测试

</details>

---

## License

MIT License. 详见 [LICENSE](LICENSE) 文件。

---

*Made with ❤️ by [wsn18381187](https://github.com/wsn18381187)*
