# Python Coding Agent：最小可运行源码包

整理日期：2026-10-29。源码来自当前项目，保留 CLI、Web 和学习中心的运行代码。
本包精简分发文件，没有改写 Agent 核心实现。

## 保留与排除

- 保留：模型适配、Agent 循环、上下文与摘要、证据选择与展开、记忆、工具、权限与 Hook、缓存、重试与熔断、会话和任务状态、附件、搜索、学习中心及 RAG。
- 保留：网页 HTML/CSS/JS、Markdown 渲染依赖及其许可证、6 份内置学习资料、依赖锁文件、无真实密钥的配置示例。
- 排除：`.venv`、模型权重、`.env`、真实密钥、会话与长期记忆数据、上传附件、用户知识库、运行日志、评测结果、大型说明文档、`evaluation` 离线评测模块和相关脚本。
- 全局／工作区里另行安装的 Skill 与扩展不是本包的一部分；Skill 管理与加载功能仍保留。内置课程是可运行资源，因此保留。
- 这是一份可编辑源码，不是包含 Python、模型和全部依赖的离线安装包。

## 1. 安装依赖

要求 Python 3.12+。从解压后的项目根目录运行，任选一种方式。

### 使用 uv

```powershell
uv sync --frozen
Copy-Item .env.example .env
```

`uv sync --frozen` 按随包 `uv.lock` 创建项目虚拟环境并安装依赖。
仅当 `.env` 尚不存在时复制模板，避免覆盖已有配置。

### 使用 Python / pip

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env
```

Linux/macOS 使用 `.venv/bin/python`。pip 的上述安装使用依赖范围，不保证与 uv 锁定版本完全相同。
不要复制其他机器的虚拟环境。若提示缺少 uvicorn，确认已经在实际启动使用的环境中安装本项目。

## 2. 配置模型

`.env.example` 是项目现有的本地 Ollama 示例，默认模型名为 `qwen3.5:4b`。
它不是原机器的真实 `.env`；原机器可能通过配置使用其他模型／服务。

```dotenv
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_MODEL=qwen3.5:4b
OPENAI_API_KEY=ollama
OPENAI_REASONING_EFFORT=none
OPENAI_MAX_OUTPUT_TOKENS=4096
OPENAI_CONTEXT_WINDOW=16384
AGENT_MAX_CONTEXT_TOKENS=9000
```

先启动 Ollama，用 `ollama list` 核对本机已有模型。模型权重需要单独部署。
如果要使用已有的 9B 模型，将 `OPENAI_MODEL` 改成实际标签，例如 `qwen3.5:9b`。
应用中的 `OPENAI_CONTEXT_WINDOW` 是预算配置，服务端上下文容量也需要对应设置。

读取 `.env` 的位置是启动命令所在目录；已有系统环境变量优先于 `.env`。
云端服务可参考 `.env.qwen37.example`，按实际账号填写地址、模型与密钥；不要把填写后的 `.env` 发给别人。

## 3. 启动网页或 CLI

先创建一个真实存在的工作目录，将路径替换成自己的项目路径：

```powershell
uv run --frozen python -m pycoding_agent.web --workspace "D:\my-project"
```

浏览器地址：`http://127.0.0.1:8765/`。关闭自动打开浏览器可加 `--no-open`。
CLI：

```powershell
uv run --frozen python -m pycoding_agent --workspace "D:\my-project"
```

pip 安装方式对应：

```powershell
.\.venv\Scripts\python.exe -m pycoding_agent.web --workspace "D:\my-project"
```

运行数据会写到所选工作区的 `.pycoding-agent/` 等运行目录；源码包本身没有历史会话数据。
同一运行实例默认监听本机回环地址。选用的模型应支持工具调用；图片理解还需要视觉能力。

## 4. 学习中心与 RAG

现有本地配置示例使用 `qwen3-embedding:0.6b`，需要在相应 Ollama 服务中单独部署。
仅检查界面和源码时，可使用无需下载模型的确定性检索后端：

```dotenv
RAG_EMBEDDING_PROVIDER=hashing
RAG_RERANK_PROVIDER=feature
```

该模式不是神经 Embedding / Cross Encoder。若启用 sentence-transformers 后端，安装可选依赖：

```powershell
uv sync --frozen --extra neural-rag
```

随后配置相应 `RAG_EMBEDDING_MODEL`、`RAG_RERANK_PROVIDER` 和 `RAG_RERANK_MODEL`；模型下载与机器资源由部署环境提供。
HTTP 重排后端通过现有环境变量配置，基础安装不需要 PyTorch。

## 5. 不调用真实模型的冒烟测试

```powershell
uv run --frozen python -m unittest discover -s tests -v
```

测试覆盖模块导入、前端静态资源、Web 初始化／健康接口／内置课程、FakeProvider 读改反馈循环和模型消息序列化。
Web 测试使用临时工作区、隔离的临时用户目录和 hashing 检索，不访问用户历史，不请求真实模型。
这些测试用于检查源码包完整性，不代表真实模型任务成功率；SWE-bench 等完整评测材料不在最小包中。

## 6. 推荐源码阅读顺序

| 入口 | 看什么 |
| --- | --- |
| `pycoding_agent/domain/` | 消息、模型上下文、工具与事件的类型 |
| `runtime/agent.py`、`runtime/loop.py` | 用户输入、决策—工具—反馈循环、继续与退出 |
| `providers/openai_compatible.py` | 请求组装、工具 Schema、流式响应与重试 |
| `runtime/context.py`、`compaction.py`、`memory.py` | 历史视图、摘要和长期记忆 |
| `runtime/coding_evidence.py`、`evidence_context.py` | 带版本的证据、预算选择与按需展开 |
| `tools/`、`runtime/hooks.py`、`security.py` | 文件与命令工具、Hook、参数和权限约束 |
| `runtime/session.py`、`task_state.py`、`tool_outputs.py` | 持久化、恢复及长输出归档 |
| `runtime/cache.py`、`circuit_breaker.py` | 缓存统计、服务熔断与恢复 |
| `learning/` | 学习进度、知识库、混合检索与重排适配 |
| `web.py`、`web_static/`、`cli.py` | 产品层组装、界面及交互入口 |

默认本地 shell 使用宿主权限；路径约束、审批和重复调用拦截不是完整操作系统沙箱。
需要更强隔离时使用已部署的 Docker 执行器，并独立核对挂载、网络与资源限制。

`SOURCE_MANIFEST.json` 记录打包来源文件的相对路径和 SHA-256。
核心运行源码、依赖定义和配置示例按原文件复制。第三方前端库许可证保留在 `web_static/` 中；本包未为项目新增开源授权条款。
