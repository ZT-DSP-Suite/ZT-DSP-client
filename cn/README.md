# ZT-DSP

**Zero Trust Dynamic Synchronization Protocol** — 官方开发语言 **Python 与 Rust**；官方实现 **ZT-DSP_PY-1.0.0** 与 **ZT-DSP_RS-1.0.0**（code 版本 **1.0.0**）｜ 遵循《ZT-DSP 协议总指导》（**docs 1.0.0**）

一个开放、零信任、端到端加密的通信协议与 Python、Rust 官方实现。基于 **PSK + X25519 + AES-256-GCM + 每包棘轮**，提供四阶段握手与全双工加密通信。

- 协议公开、实现自由、参数自治、静默丢弃
- 端到端加密：任何中继节点都无法解密通信内容
- 前向安全：X25519 临时密钥 + 每包棘轮旋转（先消耗状态后发送）
- 不依赖中心化信任锚点；令牌哈希（门牌号）经带外交换

## 文档与代码的对应关系

本实现遵循《ZT-DSP 协议总指导》，路径见 `zt_dsp_py/version.py` 的 `FOLLOWS_DOC_PATH`：

```
ZT-DSP-docs/cn/spec/ZT-DSP_1.0.0_总指导.md
```

文档与代码**不靠版本号绑定**：文档侧声明"本文档管 code 的哪些设置"，代码侧声明"本实现遵循哪份文档"。
**握手帧中不携带任何版本串**——阶段一参数 JSON 与阶段四 AAD 均不含版本或协议标识字段。

## 目录

```
├── zt_dsp_py/                  Python 官方实现（实现标识 ZT-DSP_PY-1.0.0）
│   ├── version.py             版本契约唯一事实源（docs 版本 / code 版本 / 遵循文档）
│   ├── errors.py              协议异常体系（总指导附录 H.5）
│   ├── params.py              参数集与校验（附录 F.1：七项固定顺序匹配）
│   ├── identity.py            P2P 占位令牌哈希（4.1.1）
│   ├── crypto.py              X25519 / HKDF-SHA3-256 / HMAC / AES-256-GCM
│   ├── frames.py              四类线上帧编解码 + 总时限读取（附录 F）
│   ├── handshake.py           四阶段握手状态机（附录 H.1/H.2）
│   ├── session.py             加密会话：棘轮/重放/填充/时间窗（附录 F.5/G）
│   ├── transport.py           监听/连接运行器 + 心跳聊天会话（附录 H.3/H.6）
│   ├── cli.py                 最小命令行
│   └── tests/                 pytest 套件（原语/帧/握手/会话/端到端）
├── zt_dsp_rs/               Rust 官方实现（实现标识 ZT-DSP_RS-1.0.0；平铺单 bin crate）
├── LICENSE
└── README.md
```

## 快速开始

### 依赖

- Python >= 3.10（Windows 建议 64 位）
- `pip install cryptography`

### 安装与运行

```bash
cd zt_dsp_py
pip install .                     # 或 pip install -e .
python -m zt_dsp_py --version
# → ZT-DSP_PY-1.0.0 (docs 1.0.0)

# 监听端（响应方）
zt-dsp-py --role listen --port 37291 --psk-file psk.txt

# 连接端（发起方）
zt-dsp-py --role connect --host <对端IP> --port 37291 --psk-file psk.txt

# 环境变量方式（推荐用于脚本）
set ZT_DSP_PSK=<64位hex>          # Windows
export ZT_DSP_PSK=<64位hex>       # Linux/macOS
zt-dsp-py --role listen --port 37291 --psk-env
```

**不带参数直接运行 = 交互式向导**（总指导附录 E.2，新手推荐）：依次询问角色、地址端口、
PSK（回车即生成新 PSK 并打印给对端）与协议参数，每步回车取默认值。⚠️ 当标准输入或输出被
重定向（管道、CI、IDE）时，不带参数启动只会打印用法并以退出码 0 结束，不会挂起。

进入会话后，输入消息回车发送；`/quit` 或 `Ctrl+C` 退出。本机双实例体验见总指导附录 E.5。

### 主要参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--port` | `37291` | 端口号 |
| `--random-len` | `256` | 接入随机数长度（位，8 的倍数） |
| `--random-rate` | `1024` | 随机数生成速率（次/秒） |
| `--window` | `60` | 协商窗口（秒，**双方必须一致**） |
| `--time-window` | `30` | 时间戳窗口（秒，per-peer 可配置） |
| `--padding-min/max` | 关闭 | 随机填充区间（0~2048B，可单边启用） |
| `--jitter` | `0` | 发送时序抖动（秒） |
| `--retry-count / --retry-interval` | `3` / `5.0` | 连接重试（仅发起方） |
| `--silent-hold` | `15.0` | 严格静默保持时长（秒，listen 侧握手早期静默等待） |

### 测试

```bash
python -m pytest zt_dsp_py/tests -q      # 从仓库根目录运行
```

覆盖：版本契约、派生公式（MK/EK/SID/nonce 逐字节对照总指导）、参数校验、
帧上限前置校验、Slowloris 总时限、双端握手、PSK 错误、低阶点静默、
重放/篡改拒绝、超窗棘轮前滚、单边填充互操作、心跳 165B 尺寸断言、
真实 TCP 双端流程。

## 安全要点

- **PSK 是根信任锚点**：PSK 泄露 = 全局失守。必须为恰好 32 字节高熵随机数
  （64 位 hex / Base64），通过 `--psk-file`（0600）或 `--psk-env` 注入；
  客户端拒绝公开默认值与低熵密钥。
- **带外交换门牌号**：必须通过安全渠道预先交换令牌哈希，协议不负责"发现"对端。
- 棘轮为单向（HKDF 链式派生），无 DH 自愈；发送失败即会话不可逆失步，
  必须重连（设计行为，见总指导附录 H.4）。
- 响应方对所有握手期失败执行**严格静默丢弃**（不发字节、不主动关闭、
  挂起吞字节、诊断仅本地 stderr）。

## 版本说明

| 项 | 值 |
|----|----|
| docs 版本 | `1.0.0`（本实现所遵循的总指导修订号） |
| code 版本 | `1.0.0` |
| 实现标识 | `ZT-DSP_PY-1.0.0`（语言前缀 `PY`） |
| 遵循文档 | 《ZT-DSP 协议总指导》，路径 `ZT-DSP-docs/cn/spec/ZT-DSP_1.0.0_总指导.md` |

### 命名规则体系（docs / code · 接管 / Fork 必读）

**本项目只有两个版本号**——docs 版本与 code 版本；握手帧不携带任何版本串，对端兼容性不靠版本号判断。

#### docs 版本

| 项 | 规定 |
|----|------|
| 格式 | `1.0.x`（主.次.修订） |
| 载体 | 总指导文档（独立文档仓库 `ZT-DSP-docs` 中的 `cn/spec/ZT-DSP_1.0.0_总指导.md`） |
| 现行值 | `1.0.0` |
| 修订位递增 | 澄清、勘误、可读性改进——不改变任何线上行为定义 |
| 次位递增 | 新增附录或可选章节——不改变线上行为定义 |
| 主位递增 | 协议核心语义重述（通常伴随 code 版本联动） |
| 参与网络通信 | ❌ 纯文档号 |

#### code 版本

| 项 | 规定 |
|----|------|
| 格式 | `ZT-DSP_<语言前缀>-<主.次.修订>`，简称 `code 1.0.0` |
| 载体 | **任何语言**的 ZT-DSP 实现——实现是其协议规范的具体化，规范版本与代码版本共用同一个号 |
| 现行值 | `ZT-DSP_PY-1.0.0` 与 `ZT-DSP_RS-1.0.0` |
| 语言前缀表 | `PY`=Python、`GO`=Go、`RS`=Rust、`C`=C++（**不含 C 语言与 C#**，二者须自定前缀）、`JS`=JavaScript/TypeScript、`JVM`=Java/Kotlin；其他语言自定全大写前缀，须全仓库唯一 |
| 修订位递增 | 缺陷修复、安全加固——线上字节格式**不变** |
| 次位递增 | 新增可选能力（如新挂点、填充策略）——线上格式不变或仅向后兼容追加 |
| 主位递增 | 线上字节格式变化（帧布局/派生公式变更）——新旧实现按设计互不互通（握手必然失败） |
| 多语言并存 | 不同语言的实现**可以共用同一版本号**（`ZT-DSP_PY-1.0.0` 与 `ZT-DSP_GO-1.0.0` 并存），靠语言前缀区分 |
| 参与网络通信 | ❌ 版本号本身不参与；握手帧不含任何版本串 |
| 其他语言实现 | 官方开发语言为 Python 与 Rust；新增语言实现时，在仓库根新增一个以实现标识命名的平级目录（如 `zt_dsp_go/`），与 `zt_dsp_py/`、`zt_dsp_rs/` 并列，并附协议一致性核对表 |
| 合并 / 收录建议 | fork 合并、管理者新建分支或独立实现晋升主线时，核心建议：**所有代码收纳为单文件**（一实现一文件，主线目录不新增目录树），并附协议一致性核对表 |

#### 文档-代码双向声明

握手帧不携带版本串，因此对端兼容性不靠版本号判断。文档与代码的对应关系由**双向声明**维护：

- **文档侧**：`spec/ZT-DSP_1.0.0_总指导.md` 头部声明"本文档规定 code 侧的协议行为与可调参数"。
- **代码侧**：`zt_dsp_py/version.py` 的 `FOLLOWS_DOC` / `FOLLOWS_DOC_PATH` 声明本实现遵循哪份文档。

若两端遵循的规范不一致，握手会在**阶段三确认标签**处失败。

#### 显示与引用规范

- **引用一个实现**：用 code 版本完整标识（如 `ZT-DSP_PY-1.0.0`），不要附加 docs 版本
- **`--version` 输出**（两段依次为）：code 版本实现标识、docs 版本 → `ZT-DSP_PY-1.0.0 (docs 1.0.0)`
- **引用协议行为**：写"协议行为见《ZT-DSP 协议总指导》某节"，不要引用版本串
- **禁止事项**：① 在实现标识中混入 docs 版本；② 在握手帧中写入任何版本串；③ 回收任何已用过的版本号；④ 对已发布版本做断裂式编号重置；⑤ 在 `version.py` 之外硬编码任何版本字符串

#### 唯一事实源与变更流程

- `zt_dsp_py/version.py` 是**唯一事实源**：`DOCS_VERSION`、`CODE_VERSION` / `LANGUAGE_PREFIX` / `IMPLEMENTATION_ID`、`FOLLOWS_DOC` / `FOLLOWS_DOC_PATH`
- `zt_dsp_py/tests/test_version.py` 锁定契约——改版本必须连测试一起改，测试不改则提交被拦
- 改版本的完整清单：`version.py` → `test_version.py` → 本节对应表格 → `pyproject.toml`（`version = CODE_VERSION`）→ 相关文档中的版本引用

## 许可

MIT OR Apache-2.0 双许可 — 见 [LICENSE-MIT](../LICENSE-MIT) 与 [LICENSE-APACHE](../LICENSE-APACHE)，二者择一。协议规范永久开源，不吸纳资金、不形成商业实体。
