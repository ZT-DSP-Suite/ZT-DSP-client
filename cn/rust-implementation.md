# ZT-DSP_RS-1.0.0

**Zero Trust Dynamic Synchronization Protocol** — Rust 官方实现（客户端版本 **1.0.0**，实现标识 `ZT-DSP_RS-1.0.0`）｜遵循《ZT-DSP 协议总指导》（**docs 1.0.0**）

依据《ZT-DSP 协议总指导库（1.0.0）》第四册（核心协议最小集）与附录 F/G/H（逐字节规范 / 流量分析防御 / 状态机与超时矩阵）实现的 **Rust 完整基准实现**，与官方 Python 实现 `ZT-DSP_PY-1.0.0` **线上逐字节互通**（互操作验证见下文）。同时内置基准测试（握手 / 吞吐 / 密码原语），可作为跨语言实现的性能基线。

## 与 Python 官方实现的关系

- 线上行为以 `zt_dsp_py`（ZT-DSP_PY-1.0.0）为逐字节准绳：四类帧布局、参数 JSON（默认 120B）、派生公式（MK/EK/SID/nonce 逐参数对齐）、transcript 构造、AAD/nonce 构造、心跳 165B 实测尺寸等全部一致；
- 防御规则**内建**为设计与回归测试（见下文“加固对照”）；
- 不同语言实现可共用同一代码版本号，靠语言前缀区分（docs / code 命名规则，见仓库根 README）。

## 目录

```
├── Cargo.toml / Cargo.lock 工程清单（版本 1.0.0；单 bin 目标）
├── README.md
├── zt-dsp-rs.rs            单入口：#[path] 平铺引入 + fn main + 内联集成测试
├── version.rs              版本契约唯一事实源（总指导版本 / 客户端版本 / 适用关系 / 遵循文档）
├── errors.rs               协议层错误体系（附录 H.5 的 Rust 类型化收敛）
├── params.rs               参数集与校验（F.1：七项固定顺序匹配；module_flags 上限）
├── identity.rs             P2P 占位令牌哈希（4.1.1：HMAC-SHA3-256 角色标签）
├── crypto.rs               HKDF(RFC 5869) / HMAC / AES-GCM / 恒时比较 / 熵检查
├── kex.rs                  X25519 临时密钥协商（F.3：低阶点静默、私钥 Drop 即清零）
├── frames.rs               四类线上帧编解码 + 整帧共享截止时间读取（F / H.3 Slowloris）
├── handshake.rs            四阶段握手状态机（F.2 严格静默丢弃；H.1/H.2 双状态机）
├── session.rs              加密会话：棘轮/重放/填充/时间窗/心跳（F.5 八步流水线；附录 G）
├── transport.rs            监听/连接运行器 + 三线程聊天会话（H.6 幂等清理）+ 连接限流
├── cli.rs                  最小命令行（--role/--psk-*/bench/pskgen）
├── bench.rs                基准测试（握手/吞吐/原语）
└── interop_test.py         跨语言互操作验证单文件（PY↔RS 互通 + RC1.3 断代实测）
```

> **布局说明**：全部源文件**平铺于项目根目录**（无 `src/`、`tests/`、`interop/`
> 子目录），模块经根入口 `zt-dsp-rs.rs` 的 `#[path]` 引入，集成测试内联其中。
> 本项目是**官方实现之一**，与 `zt_dsp_py/`（Python 官方实现）平级，此形态可长期保留；
> 若其他语言要新增官方实现，在仓库根新增一个以实现标识命名的平级目录即可。

## 构建

依赖：Rust 1.75+（`rustup` 默认 stable 即可），无其他系统依赖。

```bash
cargo build --release
```

> **Windows GNU 工具链注意**：项目位于含非 ASCII 字符的路径（`zt_dsp_rs/`）时，
> `x86_64-pc-windows-gnu` 的 dlltool 无法处理中文路径导致 `windows-sys` 编译失败。
> 解决方法（二选一）：
>
> ```bash
> # 方法一：把 target 目录指到 ASCII 路径（推荐）
> export CARGO_TARGET_DIR="C:/zt-dsp-rs-target"
> cargo build --release
>
> # 方法二：改用 MSVC 工具链
> rustup default stable-x86_64-pc-windows-msvc
> ```

## 快速开始

```bash
# 生成 PSK（64 位 hex）
zt-dsp-rs pskgen > psk.txt

# 监听端（响应方）
zt-dsp-rs --role listen --port 37291 --psk-file psk.txt

# 连接端（发起方）
zt-dsp-rs --role connect --host 127.0.0.1 --port 37291 --psk-file psk.txt

# 环境变量方式（推荐用于脚本）
export ZT_DSP_PSK=$(zt-dsp-rs pskgen)
zt-dsp-rs --role listen --port 37291 --psk-env
```

输入消息回车发送；`/quit`、`/exit`、`/q` 或 Ctrl+C 退出。

### 主要参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--port` | `37291` | 端口号 |
| `--random-len` | `256` | 接入随机数长度（位，8 的倍数） |
| `--random-rate` | `1024` | 随机数生成速率（次/秒） |
| `--window` | `60` | 协商窗口（秒，双方必须一致） |
| `--time-window` | `30` | 时间戳窗口（秒，per-peer 可配置） |
| `--padding-min/max` | 关闭 | 随机填充区间（0~2048B，可单边启用） |
| `--jitter` | `0` | 发送时序抖动（秒） |
| `--retry-count / --retry-interval` | `3` / `5.0` | 连接重试（仅发起方） |
| `--silent-hold` | `15` | 严格静默挂起时长（秒） |
| `--rate-limit` | `0`（关闭） | 监听侧连接速率限制（次/秒，规则 P0-6） |

PSK 注入优先级：`--psk-file`（推荐）> `--psk-env` > `--psk`（不安全）。
拒绝公开默认值与低熵密钥（熵 < 3.5 bits/byte）。

## 版本说明

| 项 | 值 |
|----|----|
| 实现标识 | `ZT-DSP_RS-1.0.0`（语言前缀 RS，见仓库根 README 命名规则体系） |
| docs 版本 | `1.0.0`（本实现所遵循的总指导修订号） |
| 遵循文档 | 《ZT-DSP 协议总指导》，路径 `ZT-DSP-docs/cn/spec/ZT-DSP-1.0.0-总指导.md` |

`--version` 输出（与 Python 实现同格式）：`ZT-DSP_RS-1.0.0 (docs 1.0.0)`

## 测试

```bash
cargo test
```

覆盖：版本契约、参数 JSON 逐字节（120B）、RFC 5869 官方向量、派生公式、
帧上限前置校验、Slowloris 整帧总时限、双端握手、PSK 错配（双端安全错误）、
参数不匹配严格静默（零字节断言）、低阶点静默（先算 DH 后回应）、重放/篡改拒绝、
超窗棘轮前滚、单边填充互通、心跳 165B 尺寸、真实 TCP 双向流程、
五类典型漏洞回归（PoC 打不穿）。

## 与 ZT-DSP_PY 互操作验证

```bash
# 先构建 release（注意上面 Windows GNU 路径提示）
python interop_test.py --rust-bin <zt-dsp-rs 可执行路径>   # PY↔RS 互通 + RC1.3 断代，--suite 可选
```

双向场景（Python 监听↔Rust 连接、Rust 监听↔Python 连接）均验证：
四阶段握手完成 + 双向消息互通（含中文）+ 优雅退出。
**已验证通过（2026-09-05，Python 3.14 / Rust 1.98 / Windows）**。

## 基准（release 构建，回环 TCP，默认参数，Windows / Rust 1.98 实测）

| 项目 | 结果 |
|------|------|
| 完整四阶段握手 | 均值 2.19 ms（P50 2.05 ms / P95 3.17 ms），约 457 次/秒 |
| 会话吞吐（16KiB/包，含每包棘轮旋转） | 78.6 MiB/s（约 5030 包/秒） |
| X25519 密钥生成+共享秘密 | 7495 次/秒 |
| HKDF-SHA3-256（32B 输出） | 23.3 万次/秒 |
| HMAC-SHA3-256 | 49.9 万次/秒 |
| AES-256-GCM（1KiB） | 加密 386 MB/s / 解密 447 MB/s |
| SHA3-256 | 284 MB/s |

复现：`zt-dsp-rs bench [--handshakes N] [--throughput-mib M] [--primitive-iters K]`

## 加固对照（相对 Python 参考实现的行为差异）

> 左列为防御规则编号（`P0-x` / `P1-x`）。

| 编号 | 问题 | 本实现的处置 |
|------|------|--------------|
| P0-3 | 静默排水可被"滴字节"永久占用 + 悬挂 FD | 排水循环以**总截止时间**约束；挂起耗尽后强制关闭 |
| P0-4 | 收发共享可变超时竞态 | 收发路径各持独立锁与预算，状态仅由 `state` 锁保护 |
| P0-6 | 无连接速率限制 | `--rate-limit` 令牌桶（默认关闭，行为与官方一致） |
| P0-8 | PSK 输入路径污点 | `--psk-env`/`--psk` 的值**永不**作为路径打开（回归测试覆盖） |
| P1-1 | 无 TCP_NODELAY | 全部连接启用 `set_nodelay(true)` |
| P1-3 | PSK 文件 BOM | 读取剥离 UTF-8 BOM |
| P1-4 | Windows 权限检查误报 | POSIX 权限告警仅在 Unix 执行 |
| P1-5 | SO_REUSEADDR 抢占端口 | Windows 不设（默认独占）；仅 Unix 启用复用 TIME_WAIT |
| P1-7 | 密钥快照不可擦除 | 全部密钥材料 `zeroize`（含发送路径的 EK 快照、HKDF 中间量） |
| 通用 | 类型化错误收敛 | `errors::Error` 枚举（H.5 异常树一一对应），对端输入零 panic |

其余协议行为（严格静默五要素、先消耗状态后发送、恒时比较、超窗前滚、
幂等清理）与 Python 参考实现语义一致，由测试逐项锁定。

## 许可

MIT OR Apache-2.0 双许可 — 见仓库根 [LICENSE-MIT](../LICENSE-MIT) 与 [LICENSE-APACHE](../LICENSE-APACHE)。
