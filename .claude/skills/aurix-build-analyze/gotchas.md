# aurix-build-analyze 陷阱与失败模式

## 1. 非商业 TASKING 许可禁止独立编译

**症状**：命令行 `make` 时出现

```text
ctc F104: protection error: License does not support running as standalone.
Please use the integrated development environment.
```

**原因**：ADS 捆绑的 TASKING Lite（v1.1r8 non-commercial）许可只允许在 IDE 进程内运行。

**处理**：
- 用 `--mode headless`（ADS 无头构建，仍需关闭 GUI 以释放 workspace）
- 或在 ADS GUI 中手动 Build
- 有商业许可时才使用 `--mode make`
- `elfsize`（打印尺寸）同样受限，因此 make 模式只构建 `FreeRTOS.elf` 目标，不构建 `secondary-outputs`

## 2. `Workspace already in use!`

**症状**：headless 构建立刻退出，输出 `Workspace already in use!`

**原因**：ADS GUI 占用了 `<workspace>/.metadata` 锁。

**处理**：
1. 关闭 AURIX Development Studio（脚本会先用 `tasklist` 检测 `AURIX-studio.exe`）
2. 若确认已关闭仍报错，删除 `<workspace>/.metadata/.lock` 后重试（ADS 异常退出会遗留锁）

## 3. 陈旧产物（比编译失败更危险）

**症状**：`analyze.py` 报「源码新鲜度」失败：某些 `.c/.h` 比 `ELF` 新。

**含义**：工程里改了代码但没有成功重编（常见于许可报错后仍去烧录）。此时 `.elf/.hex` 是旧的，烧录会得到"代码改了但行为没变"的假象。

**处理**：重新构建并确认三件产物时间戳更新；分析器会对比三件产物时间差与源码时间。

## 4. map 解析陷阱

| 现象 | 原因 | 脚本处理 |
|---|---|---|
| 符号表解析为空 | `Symbols (sorted on name)` 是 `Locate Result` 块内的子表，不是独立 banner | 按 `* ` 子标题切分后解析 |
| 找不到器件宏 | map 的命令行拆成 `arguments` 行 + `file:<id>` 续行 | 两类行都拼接 |
| 找不到 LSL | cctc 把 `--lsl-file=` 翻译成 ltc 的 `-d` | 同时匹配两种写法 |
| 节区名带 `(124)` 后缀 | map 的节区编号 | 统一剥离 `\s*\(\d+\)$` |

## 5. `mpe:dfls0` 余量为 0 不是错误

`dfls0` 是 DFI/UCB 预留区，没有 code/data，`free=0` 属正常。分析器只对"有 code 或 data"的区域做余量检查。

## 6. `vPortStartFirstTask` 可能没有符号

`port.c` 中该函数声明为 `static inline`，编译器可能内联而不产生符号。不要把它列为必须存在的符号（已在可选集合中）。

## 7. 为什么 `_START` 是 `0xa0000000`

TriCore 的启动入口是分段地址（segment `0xA`），实际代码段在 `0x8000_0000` 起的 PFlash。分析器的「入口一致」检查是 ELF `e_entry` 与 map `_START` 对比，两者都应为 `0xa0000000`。

## 8. Git Bash 下必须用 `py -3`

`python` / `python3` 在 Git Bash 中可能解析到 WindowsApps 占位 stub，无法执行（ERR-20260806-001）。所有命令统一用 `py -3`。

## 9. 路径与编码

- Windows 路径在 Python 中用 `Path`，CLI 参数支持 `C:/...` 或 `C:\...`
- map 文件按 UTF-8 + `errors=replace` 读取，避免非 ASCII 注释导致崩溃
- HEX 按 ASCII 读取

## 10. `-perspective` 参数被启动器注入

**症状**：

```text
Invalid Arguments: [-perspective, com.infineon.aurix.buildmanager.perspective.c, -cleanBuild, FreeRTOS/Debug]
Error: Unknown argument: -perspective
```

**原因**：`<ADS>/AURIX-studio.ini` 里有两行固定参数：

```ini
-perspective
com.infineon.aurix.buildmanager.perspective.c
```

CDT 的 headlessbuild 应用不认识 `-perspective`。

**处理**：复制 `AURIX-studio.ini` 为 `AURIX-studio-headless.ini` 并删掉这两行，然后：

```bash
AURIX-studioc.exe --launcher.ini <ADS>/AURIX-studio-headless.ini ...
```

`build.py` 会自动生成该 ini。

## 11. BoosterBuilder 与 CDT UI 依赖

**症状**：构建输出只有一行

```text
Managed Build system manifest file error: Could not load value handler
com.infineon.aurix.buildsystem.importexport.managed.valueHandler.AURIXToolchainValueHandler ...
```

或 `.metadata/.log` 中出现：

```text
NoClassDefFoundError: org/eclipse/cdt/ui/CUIPlugin
Caused by: IllegalStateException: Workbench has not been created yet.
```

**原因**：项目的第一个 builder 是

```xml
<buildCommand>
  <name>com.infineon.aurix.buildsystem.builders.booster</name>
```

它依赖 `org.eclipse.cdt.ui`，而该插件的 activator 需要 Workbench（GUI）。无头模式没有 Workbench，构建因此中断（exit 13）。clean 阶段不需要该 builder，所以会出现"clean 成功、build 不执行"的现象。

**处理**：构建期间临时从 `.project` 移除该 `<buildCommand>` 块，构建后恢复。`build.py` 已自动完成（备份 `.project.headless-bak`，`finally` 中恢复）。

> 手动操作时务必先备份；`.project` 在 git 中有跟踪，可用 `git checkout -- .project` 兜底。
> 若构建进程被强制终止，`.project.headless-bak` 可能残留，手动恢复：`mv .project.headless-bak .project`。

## 12. 核归属检查的两个常见误报

**误报 1：`IfxCpu_Trap_systemCall_Cpu1` 位于 PFLS0**
trap 跳转桩是共享代码，每核真正需要在本核 Flash 的是 `IfxCpu_Trap_vectorTableN`。检查已排除 `IfxCpu_Trap.*`。

**误报 2：`[.data.Cpu0_Main.g_cpuSyncEvent]` 位于 PFLS0**
方括号包裹的是初始化数据的 **ROM 拷贝镜像**（加载映像），数据本体在 DSRAM0。检查已跳过以 `[` 开头的节区。

**共享数据在 DSPR 不是硬错误**
PSPR 用于快速代码、DSPR 用于快速数据；单核设计把内核数据放在 DSRAM0 是合理的。检查将其标为 ⚠️ 而非 ❌，并提示"多核共享时应迁移到 LMU"。

## 13. 分析器不替代编译器

分析器只检查**链接结果的自洽性**，不能证明 C 代码逻辑正确。它擅长捕获：布局溢出、符号缺失、Port 接线断开、产物陈旧、HEX 损坏——这些正是"编译通过但运行异常"的高发原因。
