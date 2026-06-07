串行外设接口（SPI）
概述
SPI(Synchronous Peripheral Interface)模块主要用于与外部设备进行同步串行通信。该模块通过时钟、数据输入、数据输出和从机选择信号与外部设备进行连接。SPI模块中包含一个发送FIFO和一个接收FIFO，所需的配置和数据先写入发送FIFO，以队列的形式传输到移位寄存器，并最终发送到外部设备。同理，接收数据也先从移位寄存器保存到接收FIFO，然后以队列形式传输到总线上。该模块支持工作在主机模式、从机模式可选，可实现与外部设备的点对点通信和一主多从通信。接口时钟波特率最高为50Mhz。
图 1-1 SPI模块框图
SPI总体结构框图如上图所示。SPI模块包含配置寄存器、发送FIFO、接收FIFO、状态机和移位寄存器，其中配置寄存器、发送FIFO、接收FIFO与外部总线BUS处于同一时钟域fBUS，其时钟由系统PLL提供；状态机和移位寄存器工作在fSPI时钟域下，其时钟由外部高精度PLL提供，与fBUS异步。
配置寄存器主要用于对SPI工作模式等进行配置；发送FIFO和接收FIFO位宽都为32bits，深度都为4，与总线直接进行数据交互； SPI状态机用于控制当前所处的传输阶段；移位寄存器为32bits，在接口时钟(SCLKO/SCLKI)的控制下，将数据以串行方式发送/接收。SPI有5个中断请求线，连接到外部中断模块，分别为发送FIFO请求(TXINT)、接收FIFO请求(RXINT)、错误中断请求(ERRINT)、传输阶段转换请求(PTINT)、用户中断请求(USRINT)。
特性
SPI包含以下特性：
主、从模式选择
支持全双工、半双工、单工操作
有灵活的数据格式
数据长度：2~32 bits可编程
支持先发送LSB/MSB可选
时钟极性可选：在空闲时，时钟保持高电平/低电平
时钟相位可选：在时钟上升沿发送数据还是下降沿发送数据
波特率生成：波特率由高精度PLL产生，与系统PLL异步。最大波特率50Mhz(SCLKO/SCLKI)
5根中断线
发送FIFO中断
接收FIFO中断
用户中断
PT中断(传输阶段转换中断)
错误中断(ERR)
支持DMA传输
灵活的SPI引脚配置
硬件支持奇/偶校验选择
在从机模式下，7个从机输入通道可选
在主机模式下，16个可选的从机选择输出SS[15:0]
多个复位可选
只复位状态机
复位整个模块(发送FIFO，接收FIFO，寄存器，状态机)
从机模式下，波特率错误后传输自动停止
支持回环模式
可与市场上流行的SPI模块接口互操作
当RxFIFO满后通信停止
主机模式下，移位寄存器和RxFIFO满后可以中断通信
接收FIFO生成中断
寄存器
表 12 SPI相关寄存器
偏移地址
寄存器名
访问权限
功能描述
复位
复位值
读权限
写权限
0x0000
SPIx_CLKC
U,SV
SV,E,P
SPI时钟控制寄存器
AppRST
0x0000 0003
0x001C
SPIx_INFO
U,SV
BER
SPI信息寄存器
AppRST
0x000E 0701
0x0004
SPIx_DBG
U,SV
SV,P,OEN
SPI调试寄存器
DbgRST
0x0000 0000
0x0008
SPIx_RST0
U,SV
SV,E,P
SPI复位寄存器0
AppRST
0x0000 0000
0x000C
SPIx_RST1
U,SV
SV,E,P
SPI复位寄存器1
AppRST
0x0000 0000
0x0010
SPIx_RSTCLR
U,SV
SV,E,P
SPI复位状态清零寄存器0
AppRST
0x0000 0000
0x0014
SPIx_ACES0
U,SV
SV,SE
SPI访问使能寄存器0
AppRST
0xFFFF FFFF
0x0018
SPIx_ACES1
U,SV
SV,SE
SPI访问控制寄存器1
AppRST
0x0000 0000
0x0030
SPIx_CTL0
U,SV
SV,P
SPI控制寄存器0
AppRST
0x000F 30FF
0x0034
SPIx_CTL1
U,SV
SV,P
SPI控制寄存器1
AppRST
0x0000 0005
0x0038
SPIx_IF
U,SV
BER
SPI中断标志位寄存器
AppRST
0x0000 0000
0x003C
SPIx_IE
U,SV
U,SV,P
SPI中断使能寄存器
AppRST
0x0000 0000
0x0040
SPIx_IC
U,SV
U,SV,P
SPI中断清除寄存器
AppRST
0x0000 0000
0x0044
SPIx_ IS
U,SV
U,SV,P
SPI中断置位寄存器
AppRST
0x0000 0000
0x0048
SPIx_ SCONF
U,SV
BER
SPI从机控制寄存器
AppRST
0x0F87 1C71
0x004C + i×4
SPIx_CHCTLi
U,SV
SV,P
SPI通道控制寄存器i (i=0-7)
AppRST
0x0000 1450
0x006C
SPIx_STA0
U,SV
U,SV,P
SPI状态寄存器0
AppRST
0x0000 0000
0x0070
SPIx_STA1
U,SV
U,SV,P
SPI状态寄存器1
AppRST
0x0000 0000
0x0074
SPIx_SSCFG
U,SV
SV,P
SPI从机选择信号配置寄存器
AppRST
0x0000 0000
0x0078
SPIx_EXLCNT
U,SV
U,SV,P
SPI超长数据模式计数寄存器
AppRST
0x0000 0000
0x007C
SPIx_MCNT
U,SV
U,SV,P
SPI移动计数寄存器
AppRST
0x0000 0000
0x0080
SPIx_MCTL
U,SV
U,SV,P
SPI移动计数模式控制寄存器
AppRST
0x0000 0000
0x0084
SPIx_MIXPUSH
U,SV
U,SV,P
SPI混合数据输入寄存器
AppRST
0x0000 0000
0x088
SPIx_SCTLPUSH
U,SV
U,SV,P
SPI从机控制输入寄存器
AppRST
0x0000 0000
0x008C + i×4
SPIx_DATPUSHi
U,SV
U,SV,P
SPI数据输入寄存器i (i=0-7)
AppRST
0x0000 0000
0x00AC
SPIx_RXPOP
U,SV
BER
SPI数据输出寄存器
AppRST
0xFFFF FFFF
0x00B0
SPIx_DBGRXPOP
U,SV
BER
SPI在Debug模式下数据输出寄存器
AppRST
0x0000 0000
0x00B4
SPIx_PORTSEL
U,SV
U,SV,P
SPI端口选择寄存器
AppRST
0x0000 0000
0x00B8
SPIx_TM
U,SV
TM,SV,P
SPI测试寄存器
AppRST
0x0000 0000
0x00BC
SPIx_INTM
U,SV
U,SV,P
SPI中断模式寄存器
AppRST
0x0000 0000
基地址：0xF400 0000
基地址：0xF400 0100
基地址：0xF400 0200
基地址：0xF400 0300
SPI系统寄存器
SPIx_CLKC：SPI时钟控制寄存器
表 1-3 SPIx_CLKC：SPI时钟控制寄存器
偏移地址：0x0000复位值：0x0000 0003
SPIx_CLKC
域
位
类型
功能描述
EDIS
3
R/W
描述
休眠模式禁止位
0B
使能休眠模式
1B
禁止休眠模式
DISS
1
R/H
描述
模块禁止状态
0B
模块已使能
1B
模块已禁止
DISR
0
R/W
描述
模块禁止控制位
0B
无
1B
禁止模块
SPIx_INFO：SPI基本信息寄存器
表 1-3 SPIx_INFO：模块信息寄存器
偏移地址：0x001C复位值：0x000E 0701
SPIx_INFO
域
位
访问权限
功能描述
MODNUM<15:0>
31:16
R
描述
SPI模块编号
000EH
SPI模块编号为0x000E
MODTYPE<7:0>
15:8
R
描述
SPI模块类型信息
07H
SPI模块为0x07
MODREV<7:0>
7:0
R
描述
SPI模块版本信息位
01H
SPI模块版本信息为0x01
SPIx_DBG：SPI调试寄存器
表 1-3 SPIx_DBG：SPI调试寄存器
偏移地址：0x0004复位值：0x0000 0000
SPIx_DBG
域
位
访问权限
功能描述
DBGSTA
5
R/H
描述
DEBUG状态位
0B
不处于Debug状态
1B
处于Debug状态
DBGP
4
W
描述
DBGCTL位写保护，读出为0
0B
DBGCTL位不可写
1B
DBGCTL位可被写
DBGCTL
3:0
R/W
描述
调试模式挂起控制
0H
没有挂起
1H
硬件挂起，时钟关闭
2H
软件挂起
其他
保留
SPIx_RST0：SPI复位寄存器0
表 1-3 SPIx_RST0：SPI复位寄存器0
偏移地址：0x0008复位值：0x0000 0000
SPIx_RST0
域
位
访问权限
功能描述
RSTSTA
1
R/W
描述
复位状态
0B
模块没有复位
1B
模块已经复位
RST
0
R/W/H
描述
模块复位请求位，与RST1寄存器的RST位一起使用
0B
无动作
1B
使能模块复位
SPIx_RST1：SPI复位寄存器1
表 1-3 SPIx_RST1：SPI复位寄存器1
偏移地址：0x000C复位值：0x0000 0000
SPIx_RST1
域
位
访问权限
功能描述
RST
0
R/W/H
描述
模块复位请求位，与RST0寄存器的RST位一起使用
0B
无动作
1B
使能模块复位
SPIx_RSTCLR：SPI复位状态清零寄存器
表 1-3 SPIx_RSTCLR：SPI复位状态清零寄存器
偏移地址：0x0010复位值：0x0000 0000
SPIx_RSTCLR
域
位
访问权限
功能描述
CLR
0
W
描述
RSTSTA复位状态清除位，读出为0
0B
无动作
1B
清零RSTSTA位
SPIx_ACES0：SPI访问控制使能寄存器0
表 1-3 SPIx_ACES0：SPI访问控制使能寄存器0
偏移地址：0x0014复位值：0xFFFF FFFF
SPIx_ACES0
域
位
访问权限
功能描述
ENn(n=0~31)
n
R/W
描述
使能Master TAG ID n的事务对模块内核地址的写访问
0B
写访问没有执行
1B
写访问执行
SPIx_ACES1：SPI访问控制使能寄存器1
表 1-3 SPIx_ACES1：SPI访问控制使能寄存器1
偏移地址：0x0018复位值：0x0000 0000
SPIx_ACES1
域
位
访问权限
功能描述
ENm(m=n+32)
n
R/W
描述
使能Master TAG ID m的事务对模块内核地址的写访问
0B
写访问没有执行
1B
写访问执行
SPI通用寄存器
SPIx_CTL0：SPI控制寄存器0
表 1-11 SPIx_CTL0：SPI控制寄存器
偏移地址：0x0030复位值：0x000F 30FF
SPIx_CTL0
域
位
访问权限
功能描述
CLR
31:30
RWH
描述
复位子模块
00B
无动作
01B
只复位SPI内部逻辑
10B
只复位SPI寄存器
11B
SPI内部逻辑和寄存器都复位
CLKSEL
29
R/W
描述
时钟源选择
0B
无时钟
1B
fPER
AUTORST
27
R/W
描述
从机模式下发生波特率错误/尖峰错误时自动复位模块使能位：CTL0_EN
00B
不复位
01B
复位
MOD
26:25
R/W
描述
主机从机模式选择
00B
主机发送接收
01B
保留
10B
从机发送接收
11B
从机发送接收
EN
24
R/W/H
描述
使能位
0B
PAUSE请求
1B
RUN请求
SDOPOL
22
R/W
描述
从机模式下，空闲态下输出数据极性选择
-q
0B
从机模式下SPI未选择时MRST=0
1B
从机模式下SPI未选择时MRST=1
SRXFULL
21
R/W
描述
主机模式下，接收FIFO满时是否停止发送
0B
禁用
1B
使能
STROBE
20:16
R/W
描述
SS0延迟模式下的选通延时
00H
1
01H
2
…
1FH
32
DLY
15
R/W
描述
SS0是否使能延迟模式
0B
禁用
1B
使能
LOOPBACK
14
R/W
描述
回环模式选择位
0B
禁用
1B
使能
EXPECT
13:10
R/W
描述
超时时间长度设置
0H
26
1H
27
…
FH
221
STAINJ
9
R/W
描述
每个数据块后是否将状态寄存器STA0的高10bit(即STA0[31:22])存入接收FIFO
0B
禁用
1B
使能
PDIV
7:0
R/W
描述
SPI模块时钟预分频
00H
1分频
01H
2分频
…
FFH
256分频
SPIx_CTL1：SPI控制寄存器1
表 1-12 SPIx_CTL1：SPI控制寄存器1
偏移地址：0x0034复位值：0x0000 0005
SPIx_CTL1
域
位
访问权限
功能描述
RXMOD
13:12
R/W
描述
接收FIFO模式选择位
00B
批量搬运模式
01B
单次搬运模式
10B
同00B
11B
保留
TXMOD
11:10
R/W
描述
发送FIFO模式选择位
00B
批量搬运模式
01B
单次搬运模式
10B
同00B
11B
保留
PT2SEL
9:7
R/W
描述
触发PT2中断事件选择位
000B
主机模式：结束等待阶段； 
001B
主机模式：串行时钟极性改变
010B
主机模式：启动帧； 
011B
主机模式：发送缓冲区清空； 
100B
主机模式：填充接收缓冲区
101B
主机模式：结束帧
从机模式：SLSI停用
110B
主机模式：数据不可用，即开始期望阶段
111B
主机模式：结束期望阶段
PT1SEL
6:4
R/W
描述
触发PT1中断事件选择位
000B
主机模式：结束等待阶段；
从机模式：发送数据正在等待移位时钟
001B
主机模式：串行时钟极性改变
010B
主机模式：启动帧；
从机模式：启动第一个数据位的传输
011B
主机模式：发送缓冲区清空；
从机模式：数据从TXFIFO通过SPI移位引擎拿出
100B
主机模式：填充接收缓冲区
从机模式：接收到的数据写入RXFIFO
101B
主机模式：结束帧
从机模式：已收到最后一个数据
110B
主机模式：数据不可用，即开始期望阶段
111B
主机模式：结束期望阶段
RXTHRES
3:2
R/W
描述
接收FIFO阈值设置
00B
0
01B
1
10B
2
11B
3
TXTHRES
1:0
R/W
描述
发送FIFO阈值设置
00B
1
01B
2
10B
3
11B
4
SPIx_IF SPI中断标志位寄存器
表 1-13 SPIx_IF SPI中断标志位寄存器
偏移地址：0x0038复位值：0x0000 0200
SPIx_IF
域
位
访问权限
功能描述
USRIF
13
R/H
描述
用户中断标志位
PT2IF
12
R/H
描述
PT2中断标志位
PT1IF
11
R/H
描述
PT1中断标志位
RXIF
10
R/H
描述
接收中断标志位
TXIF
9
R/H
描述
发送中断标志位
ERRIF
8:0
R/H
描述
错误信号标志位
000H
无报错
001H
奇偶校验报错
002H
预期外的配置报错
004H
波特率报错（从机模式）
008H
TXFIFO溢出（软件报错）
010H
TXFIFO下溢（从机模式）
020H
RXFIFO溢出
040H
RXFIFO下溢（软件报错）
080H
期望阶段超时报错
100H
SLSI错位报错（从机模式）
SPIx_IE SPI中断使能寄存器
表 1-14 SPIx_IE SPI中断使能寄存器
偏移地址：0x003C复位值：0x0000 0000
SPIx_IE
域
位
访问权限
功能描述
USRIE
13
R/W
描述
用户中断使能位
PT2IE
12
R/W
描述
PT2中断使能位
PT1IE
11
R/W
描述
PT1中断使能位
RXIE
10
R/W
描述
接收中断使能位
TXIE
9
R/W
描述
发送中断使能位
ERRIE
8:0
R/W
描述
错误信号使能位
000H
不使能报错
001H
使能奇偶校验报错
002H
使能预期外的配置报错
004H
使能波特率报错（从机模式）
008H
使能TXFIFO溢出（软件报错）
010H
使能TXFIFO下溢（从机模式）
020H
使能RXFIFO溢出
040H
使能RXFIFO下溢（软件报错）
080H
使能期望阶段超时报错
100H
使能SLSI错位报错（从机模式）
SPIx_IC SPI中断清除寄存器
表 1-15 SPIx_IC SPI中断清除寄存器
偏移地址：0x0040复位值：0x0000 0000
SPIx_IC
域
位
访问权限
功能描述
USRIC
13
W
描述
用户中断清除位
PT2IC
12
W
描述
PT2中断清除位
PT1IC
11
W
描述
PT1中断清除位
RXIC
10
W
描述
接收中断清除位
TXIC
9
W
描述
发送中断清除位
ERRIC
8:0
W
描述
错误信号清除位
000H
不清除报错
001H
清除奇偶校验报错
002H
清除预期外的配置报错
004H
清除波特率报错（从机模式）
008H
清除TXFIFO溢出（软件报错）
010H
清除TXFIFO下溢（从机模式）
020H
清除RXFIFO溢出
040H
清除RXFIFO下溢（软件报错）
080H
清除期望阶段超时报错
100H
清除SLSI错位报错（从机模式）
SPIx_IS SPI中断置位寄存器
表 1-15 SPIx_IS SPI中断置位寄存器
偏移地址：0x0044复位值：0x0000 0000
SPIx_IC
域
位
访问权限
功能描述
USRIS
13
W
描述
用户中断置位位
PT2IS
12
W
描述
PT2中断置位位
PT1IS
11
W
描述
PT1中断置位位
RXIS
10
W
描述
接收中断置位位
TXIS
9
W
描述
发送中断置位位
ERRIS
8:0
W
描述
错误信号置位位
000H
不置位报错
001H
置位奇偶校验报错
002H
置位预期外的配置报错
004H
置位波特率报错（从机模式）
008H
置位TXFIFO溢出（软件报错）
010H
置位TXFIFO下溢（从机模式）
020H
置位RXFIFO溢出
040H
置位RXFIFO下溢（软件报错）
080H
置位期望阶段超时报错
100H
置位SLSI错位报错（从机模式）
SPIx_SCONF SPI从机控制寄存器
表 1-16 SPIx_SCONF SPI从机控制寄存器
偏移地址：0x0048复位值：0x0F87 1C71
SPIx_SCONF
域
位
访问权限
功能描述
SS
31:28
R/H
描述
从机选择信号设置
DATCNT
27:23
R/H
描述
数据长度设置
00H
BYTE=0时2位；XXL模式是BYTE=1时2位
01H
2位或字节
…
1FH
32位或字节
BYTE
22
R/H
描述
字节选择
0B
DATCNT是位长度
1B
DATCNT是字节长度
MSB
21
R/H
描述
端序选择
0B
LSB
1B
MSB
USRIE
20
R/H
描述
后续帧中的PT1事件用户中断使能
0B
禁用
1B
使能
PARSEL
19
R/H
描述
奇偶校验位选择
0B
偶校验
1B
奇校验
TCNT
18:16
R/H
描述
trail阶段持续时间长度设置，单位为TPER
000B
1
001B
2
…
111B
8
TPREDIV
15:13
R/H
描述
trail阶段预分频设置，1个TPER的长度
000B
1
001B
4
…
111B
16384
LCNT
12:10
R/H
描述
lead阶段持续时间长度设置，单位为TPER
000B
1
001B
2
…
111B
8
LPREDIV
9:7
R/H
描述
lead阶段预分频设置，1个TPER的长度
000B
1
001B
4
…
111B
16384
ICNT
6:4
R/H
描述
idle阶段持续时间长度设置，单位为TPER
000B
1
001B
2
…
111B
8
LPREDIV
3:1
R/H
描述
idle阶段预分频设置，1个TPER的长度
000B
1
001B
4
…
111B
16384
LAST
0
R/H
描述
当前发送的字是否为当前帧的最后一个字
000H
不是最后一个
001H
最后一个
SPIx_CHCTLi SPI通道控制寄存器i (i=0-7)
表 1-17 SPIx_CHCTLi SPI通道控制寄存器i (i=0-7)
偏移地址：0x004C + i×4复位值：0x0000 1450
SPIx_ CHCTLi
域
位
访问权限
功能描述
BIGEND
31:30
R/W
描述
大端字节序的转化配置
00B
禁用 
01B
16位大端
10B
32位大端
11B
禁用
PARCHECK
14
R/W
描述
奇偶校验检查使能位
0B
禁用 
1B
使能
SCKPOL
13
R/W
描述
空闲态下SCK极性选择
0B
空闲电平为低 
1B
空闲电平为高
SCKPHASE
12
R/W
描述
SCK相位选择
0B
禁用 
1B
使能 
CCNT
11:10
R/W
描述
在一个数据时钟周期内，C段的持续时间长度设置
00B
0 （若BCNT为0，CCNT至少为1）
01B
1 
10B
2
11B
3
BCNT
9:8
R/W
描述
在一个数据时钟周期内，B段的持续时间长度设置
00B
0 
01B
1 
10B
2
11B
3
ACNT
7:6
R/W
描述
在一个数据时钟周期内，A段的持续时间长度设置
00B
1 
01B
2 
10B
3
11B
4
BAUDPREDIV
5:0
R/W
描述
波特率预分频设置
00H
1 
01H
2 
…
3FH
64
SPIx_STA0 SPI状态寄存器0
表 1-18 SPIx_STA0 SPI状态寄存器0
偏移地址：0x006C复位值：0x0000 0000
SPIx_ STA0
域
位
访问权限
功能描述
TRANSPHA
31:28
R/H
描述
当前所处的传输阶段
0000B
等待阶段 
0001B
空闲A阶段
0010B
空闲B阶段
0011B
引导阶段
0100B
数据阶段
0101B
末尾阶段
0110B
期望阶段
0111B
引导选通阶段
1000B
末尾选通阶段
1001B
Stop阶段(主机模式下，SRXFULL配置为1，并且RXFIFO和移位buffer都满)
TPAR
27
R/H
描述
发送的奇偶校验位
RPAR
26
R/H
描述
接收到的奇偶校验位
SS
25:22
R/H
描述
指示当前活跃的从机
RXLEVEL
13:11
R/H
描述
接收FIFO中的数据数量
000B
0 
001B
1
010B
2
011B
3
100B
4 
TXLEVEL
10:8
R/H
描述
发送FIFO中的数据数量
000B
0 
001B
1
010B
2
011B
3
BITCNT
7:0
R
描述
已经传输的bit数量
SPIx_STA1 SPI状态寄存器1
表 1-19 SPIx_STA1 SPI状态寄存器1
偏移地址：0x0070复位值：0x0000 0000
SPIx_ STA1
域
位
访问权限
功能描述
SPDETECT
3
R/W/H
描述
尖峰检测
0B
未检测到尖峰
1B
检测到尖峰
SPDETECTEN
2
R/W
描述
尖峰检测使能
0B
禁用
1B
使能
BDDETECT
1
R/W/H
描述
波特率检测
0B
未检测到尖峰
1B
检测到尖峰
BDDETECTEN
0
R/W
描述
波特率检测使能
0B
禁用
1B
使能
SPIx_SSCFG SPI从机选择信号配置寄存器
表 1-20 SPIx_SSCFG SPI从机选择信号配置寄存器
偏移地址：0x0074复位值：0x0000 0000
SPIx_ SSCFG
域
位
访问权限
功能描述
SSEN
31:16
R/W
描述
对应的从机选择信号是否使能
SSLEVEL
15:0
R/W
描述
对应的从机选择不使能时的电平值
SPIx_EXLCNT SPI超长数据模式计数寄存器
表 1-21 SPIx_EXLCNT SPI超长数据模式计数寄存器
偏移地址：0x0078复位值：0x0000 0000
SPIx_ EXLCNT
域
位
访问权限
功能描述
CURRCNT
31:16
R
描述
超大数据模式下，当前剩余的待传输字节数量
0000H
0字节
0001H
2字节
0002H
3字节
…
FFFEH
65535字节
FFFFH
65536字节
DATCNT
15:0
R/W
描述
超大数据模式下，当前剩余的待传输字节数量
0000H
2字节
0001H
2字节
0002H
3字节
…
FFFEH
65535字节
FFFFH
65536字节
SPIx_MCNT SPI移动计数寄存器
表 1-22 SPIx_MCNT SPI移动计数寄存器
偏移地址：0x007C复位值：0x0000 0000
SPIx_ MCNT
域
位
访问权限
功能描述
CURRCNT
28:16
R/H
描述
移动计数模式下，当前剩余的待传输的短数据字段
0000H
0个短数据
0001H
1个短数据
0002H
3个短数据
…
1FFEH
8190个短数据
1FFFH
8191个短数据
MOVECNT
15:0
R/W
描述
移动计数模式下，当前剩余的待传输短数据字段
0000H
无意义
0001H
1个短数据
0002H
2个短数据
…
1FFEH
8190个短数据
1FFFH
8191个短数据
SPIx_MCTL SPI移动计数模式控制寄存器
表 1-23 SPIx_MCTL SPI移动计数模式控制寄存器
偏移地址：0x0080复位值：0x0000 0000
SPIx_ MCTL
域
位
访问权限
功能描述
MOVEN
31
R/W
描述
移动计数模式使能位
TRAIL2EN
30
R/W
描述
插入末尾阶段2使能位
INTALIS
23
W
描述
置位INTALIF
INTALIC
22
W
描述
复位INTALIF
INTALIF
21
R/H
描述
在最后一个之后的中断状态标志位
0B
无处理
1B
触发事件
INTALIE
20
R/W
描述
在最后一个之后的中断状态使能
0B
禁用
1B
启用
INTBLIS
19
W
描述
置位INTBLIF
INTBLIC
18
W
描述
复位INTBLIF
INTBLIF
17
R/H
描述
在最后一个之前的中断状态标志位
0B
无处理
1B
触发事件
INTBLIE
16
R/W
描述
在最后一个之前的中断状态使能
0B
禁用
1B
启用
TCNT2
5:3
R/W
描述
末尾阶段2时间长度设置，单位为TPER
000B
1
001B
2
…
111B
8
TCNT2
5:3
R/W
描述
末尾阶段2预分频设置，TPER的长度
000B
1
001B
4
001B
16
…
111B
16384
SPIx_MIXPUSH SPI混合数据输入寄存器
表 1-24 SPIx_MIXPUSH SPI混合数据输入寄存器
偏移地址：0x0084复位值：0x0000 0000
SPIx_ MIXPUSH
域
位
访问权限
功能描述
DAT
31:0
R/W
描述
TXFIFO输入数据
8SPIx_SCTLPUSH SPI从机控制输入寄存器
表 1-25 SPIx_SCTLPUSH SPI从机控制输入寄存器
偏移地址：0x0088复位值：0x0000 0000
SPIx_ SCTLPUSH
域
位
访问权限
功能描述
DAT
31:0
R/W
描述
TXFIFO输入数据
SPIx_DATPUSHi SPI数据输入寄存器i (i=0-7)
表 1-26 SPIx_DATPUSHi SPI数据输入寄存器i (i=0-7)
偏移地址：0x008C + i×4复位值：0x0000 0000
SPIx_ DATPUSH
域
位
访问权限
功能描述
DAT
31:0
R/W
描述
TXFIFO输入数据
SPIx_RXPOP SPI数据输出寄存器
表 1-27 SPIx_RXPOP SPI数据输出寄存器
偏移地址：0x00AC复位值：0xFFFF FFFF
SPIx_ RXPOP
域
位
访问权限
功能描述
DAT
31:0
R
描述
RXFIFO读出数据
SPIx_DBGRXPOP SPI在Debug模式下数据输出寄存器
表 1-28 SPIx_DBGRXPOP SPI在Debug模式下数据输出寄存器
偏移地址：0x00B0复位值：0x0000 0000
SPIx_ DBGRXPOP
域
位
访问权限
功能描述
DAT
31:0
R
描述
RXFIFO读出数据输入数据
SPIx_PORTSEL SPI端口选择寄存器
表 1-22 SPIx_PORTSEL SPI端口选择寄存器
偏移地址：0x00B4复位值：0x0000 0000
SPIx_ MCNT
域
位
访问权限
功能描述
SLSIS
14:12
R/W
描述
从机模式下，从机选择输入端口
000B
无输入
001B
选择端口1
010B
选择端口2
011B
选择端口3
100B
选择端口4
101B
选择端口5
110B
选择端口6
111B
选择端口7
SCIS
10:8
R/W
描述
从机模式下，时钟输入端口选择
000B
选择端口1
001B
选择端口2
010B
选择端口3
011B
选择端口4
100B
选择端口5
101B
选择端口6
110B
选择端口7
111B
选择端口8
SRIS
6:4
R/W
描述
从机模式下，从机接收端口选择
000B
选择端口1
001B
选择端口2
010B
选择端口3
011B
选择端口4
100B
选择端口5
101B
选择端口6
110B
选择端口7
111B
选择端口8
MRIS
3:0
R/W
描述
主机模式下，主机接收端口选择
0000B
选择端口1
0001B
选择端口2
0010B
选择端口3
0011B
选择端口4
0100B
选择端口5
0101B
选择端口6
0110B
选择端口7
0111B
选择端口8
1000B
选择端口9
1001B
选择端口10
1010B
选择端口11
1011B
选择端口12
1100B
选择端口13
1101B
选择端口14
1110B
选择端口15
1111B
选择端口16
SPIx_TM：测试寄存器
表 131 SPIx_TM：测试寄存器
偏移地址：0x00B8复位值：0x0000 0000
SPI_TM
域
位
访问权限
功能描述
TMSEL
4：1
R/W
描述
测试引脚功能位
0000B
conf_using[7:0]
0001B
conf_using[15:8]
0010B
conf_using[23:16]
0011B
conf_using[31:24]
0100B
{操作模式状态机[2:0], short_mode, master_mode_b2s, slave_mode_b2s, mix_mode, conf_data_mode}
0101B
主机状态机[7:0]
0110B
{1'b0, timeout_en, spi_master_state[13:8]}
0111B
{pt2if_spi, pt1if_spi, load_pha_dly, c_end_time, mi, sample_en, ss_n, sck_flip}
1000B
{load_shift_buff_dly, shift_en_s, sample_en_s, si_s_sample, so_dir, spi_slave_state}
1001B
{3'b0, spike_err_bus, spike_err_spi, baud_err_bus, baud_err_spi, ssi_inact_err_spi}
1010B
txfifo_state[7:0]
1011B
{fifo_in_flag, rd_en_tx_m_s, wr_en_tx, fifo_empty_tx, fifo_full_tx, spi_if_txif_hw_val, txfifo_state[9:8]}
1100B
{fifo_cnt_tx, bit_width_temp}
1101B
{spi_if_rxif_hw_val, fifo_cnt_rx, rd_en_rx, wr_en_rx, fifo_empty_rx, fifo_full_rx}
1110B
{app_rst_n_bus, debug_rst_n_bus, genreg_rst_n_bus, logic_rst_n_spi, inter_rst_n_bus, spi_spiclk_enable, spi_module_busclk_en_genreg, spi_module_busclk_en}
其他
8’b0
TMEN
0
R/W
描述
测试模式使能
0b
无作用
1b
使能测试模式
SPIx_INTM SPI中断模式寄存器
表 1-13 SPIx_INTM SPI中断模式寄存器
偏移地址：0x00BC复位值：0x0000 0000
SPIx_INTM
域
位
访问权限
功能描述
USRIM
4
R/W
描述
用户中断模式选择位
0B
中断信号为电平
1B
中断信号为脉冲
PTIM
3
R/W
描述
PT中断模式选择位
0B
中断信号为电平
1B
中断信号为脉冲
RXIM
2
R/W
描述
接收中断模式选择位
0B
中断信号为电平
1B
中断信号为脉冲
TXIM
1
R/W
描述
发送中断模式选择位
0B
中断信号为电平
1B
中断信号为脉冲
ERRIM
0
R/W
描述
错误中断模式选择位
0B
中断信号为电平
1B
中断信号为脉冲
功能描述
时钟域
SPI状态机位于独立的频域，其工作频率fPER由外围锁相环生成，该时钟与fBUS完全异步。波特率由fPER分频生成，分频系数至少为4。
 
图 1-2  SPI时钟域框图
主机模式状态机
主机模式下，SPI模块生成时序，串行时钟以及从机片选信号。
一次通信过程的时序
配置SPI通信需要有下列参数：定时延迟，数据长度，占空比及数据采样。
1个SPI帧从一个从机片选信号SS有效开始，到SS失效结束。SS在idle转变到leading时转换为有效，在trailing到wait或者idle时转换为失效。1个序列包括五个阶段：idle延迟，leading延迟，数据阶段，trailing延迟和一个可选择的wait阶段。Idle阶段细分为两个等长的阶段：idle A和idleB。
SPI灵活的定时控制允许在非常宽的时间范围内编程每一个相位，且具有足够的精度。在考虑时钟不对称性和环路延迟的情况下，可以在一定程度上提高系统的最高波特率。CHCTLi（i=0-7）的位域A,B,C定义了对应位段的长度。采样点始终位于B段和C段的过渡位置，并且时钟的占空比由A段和B+C段定义。
相位的长度是使用寄存器SCONF中相应的位域来配置的。在tQ单位中，有四个主要的位字段定义了相位的长度，几个修饰位字段定义了它们的范围和颗粒度：IDLE、LEAD、DATA、TRAIL。WAIT阶段是等待写进Tx FIFO的一个简单循环，因此没有预定义的持续时间，也就没有定义位字段。IDLE位域定义了两个长度相同的子阶段IDLE A和IDLE B。它们之间的分界线是下一个从端串行时钟信号的极性变化。
采样点控制的目的是允许从机在尽可能高的波特率下可靠地接收传输的数据。
图 1-3 数据长度为4位的SPI帧结构
时钟极性由位域CHCTLi（i=0-7）.SCKPOL配置。该位域将时钟空闲极性设置为低或高。时钟相位由位域CHCTLi（i=0-7）.SCKPHASE配置。该位域将初始化时钟延迟设置为0或对应CHCTL的位段A。
SCKPOL和SCKPHASE的设置控制主机端。从机模式的时序行为固定为SCKPOL=1和SCKPHASE=0，这些值必须在SCONF.SS指向的CHCTLi（i=0-7）中配置。CHCTLi（i=0-7）.ACNT,BCNT,CCNT不会影响从机端的采样点。采样点位于SCLKI的下降沿。
图 1-4 数据长度为4位且SCKPHASE=0的传输时序
SCKPHASE=0时，SS的有效沿到第一个时钟沿的距离为LEAD+CHCTLi.A。
SCKPHASE=0时，最后一个时钟沿到SS的失效沿的距离为TRAIL。
CHCTLi（i=0-7）.SCKPHASE=1是用来与从机端通信，这种从机端在被SS信号选中后，立即发送一个随机值或未规范的值。在这种情况下，从机端使用帧中的第一个时钟沿移位出第一个有效数据位。第二个沿锁存该位值，以此类推。帧中的末尾沿用于锁存最后一个有效数据位，该位通常保持驱动到帧结束。
图 1-5 数据长度为4位且SCKPHASE=1的传输时序
SCKPHASE=1时，SS的有效沿到第一个时钟沿的距离为LEAD。
SCKPHASE=1时，最后一个时钟沿到SS的失效沿的距离为TRAIL+CHCTLi.BCNT+CHCTLi.CCNT.
数据采样点
外部串行时钟的占空比和主机端的RX数据采样点，取决于CHCTLi中的ACNT、BCNT和CNT数值。如下规则计算采样点：
BCNT为0时，采样点位于A段与C段间隔点。
BCNT非0时，采样点位于B段与C段间隔点。
数据传输模式
三种数据传输模式：短数据、长数据、连续数据模式，其状态机切换如下图：
图 1-6 三种数据模式的状态机切换
注：仅短数据模式支持奇偶校验；
通道扩展
16个从机片选通道由均分为两组：
通道0-通道7为第一组；
通道8-通道15为第二组，其配置为CHCTL(y-8)(y=8-15)。
波特率及时域控制
根据TPER=1/fPER,每路SPI从机片选通道都可以定义自己的时序及波特率
TSCLKz=TPER × CTL0.PDIV × CHCTLi(i=0-7). BAUDPREDIV ×(ACNT+BCNT+CNT) 公式 1-1
TLEAD= TPER × SCONF. LPREDIV×SCONF.LCNT公式 1-2
TTRAIL= TPER × SCONF. TPREDIV×SCONF.TCNT公式 1-3
TIDLE= TPER × SCONF. IPREDIV×SCONF.ICNT公式 1-4
TSTROBE=TPER × CTL0.PDIV × CHCTLi(i=0-7). BAUDPREDIV ×CTL0.STROBE公式 1-5
图 1-6 分频控制
波特率可以采取另一种计算方法。如下：
公式 1-6
注意：每位的长度至少为4倍的TPDIV。从机模式下，至少为5倍的TPDIV。
每个工作通道的延迟使用下列公式计算。
TLEAD= TPER × 4 SCONF.LPREDIV×（SCONF.LCNT+1）公式 1-7
TIDLE= TPER × 4 SCONF.IPREDIV×（SCONF.ICNT+1）公式 1-8
TTRAIL= TPER × 4 SCONF.TPREDIV×（SCONF.TCNT+1）公式 1-9
从机模式
从机模式通过设置位字段CTL0.MOD为1x进入。在进入从机模式前，需要配置相关参数，包括SCLKI、SLSI、MTSR引脚选择、引脚输入电平、上拉下拉配置等。配置应在开始数据传输之前完成。只有当模块处于等待状态时，才允许重新配置。随后进行状态机复位，然后进入从机模式。
从机模式下，经由外部主机端的串行引脚输出或输入模块。RXFIFO必须由系统定期清空，以避免数据丢失。TXFIFO必须由系统定期填入，以避免TXFIFO空时会传输全1的数据。
若从机模式需要一个从机片选信号来标记帧起始，并与位计数并行标记帧结束，那么主机的停用从机信号会自动将移位寄存器状态机重置为等待状态。
若冲击模式需要比特计数来确定帧的结束，那么任何SCLKI时钟周期长度超过两个比特的时间都会被视为帧结束，同时也被当做波特率错误处理。
在从机模式下，模块依据外部的时钟沿直接进行响应。所以，leading，trailing，idle延迟和占空比及采样点的设置都是互不相关的。在所有时序设定中，只有数据长度和波特率分频器设置是相关的。因为波特率设置是负责输入串行时钟的看门狗定时器工作，所以它的配置尤为重要。
通常从机模式支持与主机模式相同的用户界面。这就意味着SCONF-Data的序列保持不变。SRF位此时会忽略掉。
将从机模式下的数据长度设置限制在2-32位。SCONF.BYTE设置为0。
若工作在单工接收状态，用户软件必须重启模块，以便切换到全双工状态。通常模式配置需要模块重启，包括重置内部状态机和计数器。
从机发送时，用户软件必须在帧的第一个SCLKI边缘到达之前将数据写入TXFIFO。若此时TXFIFO为空，则发生下溢，发出为1的数据，若启用了错误中断此时会触发下溢错误中断。若TXFIFO在第一个SCLKI边缘开始移位的同时写入，在发生下溢，将触发中断，并且从TXFIFO传输的数据可能是已损坏的，即首位为1。
TXFIFO/RXFIFO下溢时，传输的数据全为1.
TXFIFO/RXFIFO溢出会导致最后的数据丢失。此时RXFIFO中的数据或状态可能会丢失
从机模式下的位计数按照以下规则进行：
对传入的位进行计数的情况下，当达到SCONF.DL中定义的值时，这些位在RXFIFO中进行传输。
若SLSI输入被禁用，则重置内部位计数器。
在从机模式下，只有当没有待处理的传输队列和待处理的传输且TXFIFO位空时，才会使能睡眠请求。
从机支持三线模式，即不需要片选信号。通过将PORTSEL_SLSIS配置为0进入三线模式。三线模式下发送数据时，SCKPHASE=0的模式下第一个bit是默认值，不是想要发送的值；
从机模式的移位时钟相位及极性
在从机模式下，支持极性和相位相互组合：{SCKPOL, SCKPHASE}={0,0}、{0,1}、{1,0}、{1,1}。
注：当{SCKPOL, SCKPHASE}={0,0}、{1,0}时，要求片选拉低时刻到第一个sck变化时刻的时间至少是4个spi_clk周期，以保证主机能采样到从机输出的第一比特数据。
波特率监测
本模块提供两种机制来监控从机模式下的移位时钟输入信号。
接收移位时钟频率是否在一定范围内
移位时钟输入是否有尖峰
在波特率过高错误时，用户软件可以激活复位，波特率检测和尖峰电位检测都会受影响，其中尖峰电位检测更有效。尖峰电位检测反应迅速，波特率检测需要几个波特率比较高的比特位。波特率检测使用两个标称比特倍宽的窗口，并统计实际比特数：检测到双倍波特率错误需要至少4个移位时钟脉冲的时间，四倍波特率错误则需要8个。
波特率检测不会对小于一个内核时钟周期的尖峰做出反应。当波特率过低时，波特率错误检测立即作出反应，尖峰点位检测则会忽略这种情况。
波特率错误检测
若移位时钟的波特率小于预期波特率的一半或超过预期波特率的两倍，则：
在STATUS.ERRORFLAGS中置位响应的标志位
如果CTL01.ERRORENS中使能了错误中断，则触发错误中断
如果CTL0.AUTORST中使能了自动清零CTL0.EN，则将其清零。
尖峰检测
尖峰检测分为两种：
检测到RXFIFO中的数据数量在一个周期内增加了2；
使用反向看门狗：在反向看门狗计数器的计数范围内出现了时钟边沿；
在SCLKI到最后25%阶段出现峰值，当看门狗停止时，会触发看门狗根据峰值进行计数。那么下一个时钟边缘就会触发一个尖峰事件。应遵循如下规则：
50%×TSCLKI <CHCTL.BCNT+ CHCTL.CCNT<100%×TSCLKI
移位时钟监测标志位
波特率错误标志位IF.ERRIF[2]被标志位清零位FLAGSCLEAR.ERRORCLEARS[2]写清后，标志位STA1.BRDETECT和STA1.SPDETECT自动清零
奇偶校验
对每个从机奇偶校验是否使能可配置(使能奇偶校验时，发送bits由2~32扩展为3~33bits)。奇偶校验位被放置在数据的LSB位置。当MSB=0时，先发送奇偶校验位；当MSB=1时，最后发送奇偶校验位。
最新接收和发送的奇偶校验值可读，如果未使能奇偶校验，则读到0。
注：奇偶校验只支持短数据模式；
操作模式
SPI模块传输由DMA模块提供的任意长度的RAM队列。当SPI模块收到关闭时钟或暂停模块的请求，它将禁用所有服务请求命令。
SPI模块可用硬件挂起和软件挂起来关闭时钟或暂停模块。该请求可以由硬件信号和软件写CTL0.EN位来触发。
工作态切换
模块支持三种工作状态-Disable、Pause、Run：
Disable状态下，SPI模块关闭，所有的服务请求都无效
Pause状态下，支持访问寄存器和FIFO，与外部设备相连的信号不发生变化；发送/接收状态机不活跃
Run状态下SPI正常运行，此时CLC_DISR==0 && CTL0_EN==1
图 1-6 Pause和Run切换概览
注：Sleep模式下，SPI进入Pause状态，时钟fBUS和fPER都关闭；从Sleep模式唤醒后，SPI处于Pause状态，时钟fBUS和fPER都打开。
模块进入sleep状态的机制如下：
主机模式：
若传输正在进行中，那么在TRAIL延迟结束后进入sleep状态
若模块未工作，那么直接进入sleep状态
从机模式：
已经完全接收到了SCONF.DATCNT中要求数量的数据之后，进入sleep状态
若模块未工作，也没有传输正在进行，移位寄存区为空且TXFIFO也是空，那么立即进入sleep状态
SS信号为不工作状态，那么立即进入sleep状态
模块禁用的机制如下：
主机模式：
若传输正在进行中，那么在TRAIL延迟结束后进入禁用状态
若模块未工作，那么直接进入禁用状态
从机模式：
若传输正在进行中，已经完全接收到了SCONF.DATCNT中要求数量的数据之后，进入禁用状态
若模块未工作，也没有传输正在进行，移位寄存区为空且TXFIFO也是空，那么立即进入禁用状态
OCDS挂起
总线可以读取SPI FIFO，但是此时FIFO的数据和读/写指针不会改变。
OCDS硬挂起：简单的将SPI模块冻结在当前状态，所有信号不再改变，包括传输线上的信号；
SPI核时钟立即关闭；
支持对寄存器写操作，但是会引入几个周期的核时钟fBUS，对SPI状态产生影响；
支持对寄存器读操作，且对SPI状态无影响；
OCDS软挂起：SPI在子序列TRAIL阶段结束后立即进入PAUSE状态，并发送应答信号；
模块只是暂停状态，SPI核时钟fBUS处于打开状态；
读/写会导致状态机的变化；RXFIFO会对读访问作出反应
FIFO功能
本模块有1个4×32位TX FIFO和1个4×32位RX FIFO。
TX FIFO写入规则：
DATA_PUSH:对这8个功能相同的位置的写操作总被认为是数据写入。但是写入过程需要遵守以下规则：
DATA_PUSH0~DATA_PUSH7需要按顺序写入；
DATA_PUSH不必全部使用，但一定是从DATA_PUSH0开始使用；
即可以只使用DATA_PUSH0；可以只使用DATA_PUSH0~DATA_PUSH1；可以只使用DATA_PUSH0~DATA_PUSH2；依次类推；但是不能在不使用DATA_PUSHn的情况下使用DATA_PUSHn+1(这里n=0~6)；
SCONF_PUSH:对该位置的写操作被认为是配置。
MIX_PUSH:依据规则决定该位置的写操作是数据还是配置。
注：可以选择将SCONF_PUSH和DATA_PUSH配合使用写TXFIFO，也可以只MIX_PUSH写TXFIFO，但是不能将MIX_PUSH与SCONF_PUSH、DATA_PUSH混合使用；
RXFIFO读取规则：
RX_EXIT:依据规则决定该位置的读操作是数据还是配置。
以下为SPI工作模式和TXFIFO目标地址的使用规则。
短模式：MIX_PUSH，DATA_PUSH/ SCONF_PUSH
长模式：MIX_PUSH，DATA_PUSH/ SCONF_PUSH
连续模式：MIX_PUSH，DATA_PUSH/ SCONF_PUSH
单配置多帧模式：MIX_PUSH
XXL模式：DATA_PUSH/ SCONF_PUSH，MIX_PUSH
自动计数模式：DATA_PUSH/ SCONF_PUSH
注：如果使用MIX_PUSH写TXFIFO，软件必须严格保证向TXFIFO中写入的DATA数量与SCONF中配置的待传输数据量匹配，否则，可能会出现将SCONF误认为DATA，或将DATA误认为SCONF的情况。任何模式下都一样。
Tx_FIFO由配置项和数据项填充。在Tx_FIFO退出时分发给SCONF和移位寄存器。TXFIFO依据配置/数据项进行跟踪。控制和数据元素自动分配到SCONF和移位寄存器中。若无数据可用，在新的SCONF等待执行。
若在帧结束时FIFO中仍有数据：
在短模式时，新的帧数据将依据前一个配置自动发送。
在长模式时，多余的数据被忽略。
TXFIFO的错误情况：
当MIX_PUSH、SCONF_PUSH、DATA_PUSHn中的数据没有存入TXFIFO的情况下，软件再次写该寄存器，则产生TXFIFO上溢错误(这里n=0~7)；该寄存器之前的数据被覆盖。
在从机模式时，发生下溢则从TXFIFO读出全“1”。
RXFIFO的错误情况：
从空的RXFIFO读取的FPI总线生成了下溢中断，并且读取的值全“1”。
硬件试图将数据或状态写入已满的RXFIFO时会生成溢出中断。写入操作被忽略。
若CTL0.SRF置位，在主机模式下FIFO填满时通信会停止。在从机模式下，该位无效。
若FPI总线频率很慢，然而波特率却很高，在移位寄存器和未满的RXFIFO之间可能会发生数据丢失的情况，此时，虽然RXFIFO未满，但是也会产生一个溢出中断。
依据CTL0.SI位，Rx_FIFO可以包含状态和接收到的数据项。
注意：若TXFIFO填入的是8位或16位的数据，则数据被1:1映射到其32位宽的TXFIFO地址，非数据部分用0填充。
图 1-9 FIFO工作示意
短数据模式
SCONF.LAST=1，SCONF.BYTE=0配置为短数据模式。传输的数据长度2~32位。
图 1-10 短数据模式操作
框图说明（FIFO未满时执行）：
为帧起始，可配置DMA和SPI通道，或DMA直接触发两次搬运（配置和数据，此时不需要②阶段）
触发DMA搬运一次数据
DMA直接触发两次搬运（配置和数据，此时不需要②阶段），或配置2次DMA搬运
触发DMA搬运一次数据
长数据模式
SCONF.LAST=1，SCONF.BYTE=1配置为长数据模式。最多可传输32字节数据。
可通过使用XXLCON寄存器扩展最大数据
图 1-11 长数据模式操作
框图说明（FIFO未满时执行）：
为帧起始，使能DMA通道，配置5次SPI的DMA搬运
SPI触发DMA搬运5次数据
在长数据模式下，使用SCTL_PUSH和DATA_PUSH方式写TXFIFO时，当需要一个数据但TXFIFO中写入的是配置时，会产生预期外的配置报错。超大数据模式和连续数据模式 & BYTE=1时同样适用。
连续数据模式
SCONF.LAST=0配置为连续数据模式。连续模式下，可发送任意长度的数据流，并且同时激活从端片选信号。在长短数据模式下都可用。每个数据块后(倒数第二个数据块除外)重复发送第一个SCONF，紧接着再发送后续数据。倒数第二个数据块后发送新的SCONF，此时的SCONF_LAST位为1，表示下一个发送的数据块为最后一个数据块。
图 1-12 连续数据模式操作
框图说明（FIFO未满时执行）：
为帧起始，配置DMA通道搬运SPI数据
SPI或定时器触发DMA搬运
配置DMA通道搬运SPI数据或者直接禁用SPI模块
单配置多帧模式
SCONF.LAST=1，SCONF.BYTE=0，SCONF.DATCNT≤15配置为单配置多帧模式。帧数据最大16位，高16位数据全“0”。
自动计数模式
SCONF.LAST=0，SCONF.BYTE=0，MCCON.MCEN=1配置为自动计数模式。在自动计数模式下，当一帧传输完成后，从机选择信号SS自动转到不活跃状态。计数器MOVECNT范围为1~8191，向下计数。MOVECNT表示本次事务要传输的数据量为MOVECNT个短数据。
也可将连续长数据模式与自动计数模式的混合：以连续长数据模式开始，以自动计数模式结束。
大端数据格式
CHCTLi(i=0-7).BIGEND激活写入移位寄存器的数据字节转换，并从移位寄存器读取大端序格式。CHCTLi(i=0-7).BIGEND允许在每个从端之间切换大小端序。
图 1-13 大小端转换
回环模式
回环模式是主机模式的测试特性，用于在发送和接收信号之间建立模块内部连接，类似于发送和接收引脚短接。CTL0.LOOPBACK置位激活回环。
中断
有5个中断线连接到中断模块-TX中断、RX中断、用户中断、PT中断、错误中断(ERR)。
图 1-14 中断示意图
从机模式SLSI中断
在从机模式下，如果启用了PT2，取消激活SLSI信号触发PT中断。
TXFIFO中断的生成
TXFIFO提供两种生成方式，由CTL1.TXFM配置。
单搬运模式：通过在TXFIFO有空闲空间时就立即触发中断写TXFIFO，保持TXFIFO尽量处于满状态。单搬运模式下每次中断只向TXFIFO中搬一个数据。
批量搬运模式：通过在TXFIFO有多个空闲空间时触发中断来减少中断数量。在批量搬运模式中，当TXFIFO中的数据量低于配置的阈值(阈值等于CTL1_TXTHRES+1)时，并且此时SPI_IF_TXIF为0时，触发中断。这就意味着每次中断至少可以向TXFIFO中搬(4-CTL1_TXTHRES)个数据。
RXFIFO中断的生成
RXFIFO提供两种生成方式，由CTL01.RXFM配置。
单搬运模式：RXFIFO中有数据时即触发中断读RXFIFO使RXFIFO尽量处于空状态。单搬运模式下每次中断只从RXFIFO中读一个数据。
批量搬运模式：通过检测到RXFIFO中有多个数据时触发中断来减少中断数量。在批量搬运模式中，当RXFIFO中的数据量高于配置的阈值(阈值等于CTL1_RXTHRES)时，并且此时SPI_IF_RXIF为0时，触发中断。这就意味着每次中断至少可以从RXFIFO中读(CTL1_RXTHRES+1)个数据。
模块复位
模块有两个复位源：
BPI寄存器KRST0/KRST1，BPI复位会让整个SPI模块复位。复位通用寄存器和模块逻辑功能。
寄存器复位CTL0.RST。对应的配置位选择是复位TX_FIFO、RX_FIFO、协议状态机还是复位通用寄存器。
典型场景使用说明
主机模式
打开时钟：
clkc_disr = 0; //该步骤操作的前提是CPU处于SV模式，并且SCU配置为endinit阶段
配置ctl0寄存器：
ctrl0_clksel = 1;
ctrl0_mod = 2'b00; //主机模式
ctrl0_pdiv = 3; //对工作时钟分频：4分频
配置ctl1寄存器：
ctrl1_txmod = 1; //txfifo中断触发模式
ctrl1_rxmod = 1；//rxfifo中断触发模式
配置sscfg寄存器：
sscfg_ssen = 16’h0003; //将使能从机0/1；
sscfg_sslevel =16’hffff; //从机不使能时片选信号为全1；
配置portsel寄存器：
portsel_misel = 3’d0;//主机选择数据输入端口0：spi_mrst1；时钟线：spi_sclk；数据输出线spi_mtsr；
与spi_slso0、spi_slso8所挂载的从机进行传输时的特性，通过chctl0进行配置：
chctl0_bigend = 0；//小端模式
chctl0_parcheck = 0； //禁用奇偶校验
chctl0_sckpol = 0; //极性0
chctl0_sckphase = 1; //相位1
chctl0_ccnt = 1； //阶段C长度1
chctl0_bcnt =0；  //阶段B长度0
chctl0_acnt = 1; //阶段A长度1
chctl0_baudprediv = 3; //ctrl0_pdiv分频的基础上再进行4分频；
与spi_slso1、spi_slso9所挂载的从机进行传输时的特性，通过chctl1进行配置：
chctl1_bigend = 0；//小端模式
chctl1_parcheck = 1； //禁用奇偶校验
chctl1_sckpol = 1; //极性0
chctl1_sckphase = 1; //相位1
chctl1_ccnt = 1； //阶段C长度1
chctl1_bcnt =0；  //阶段B长度0
chctl1_acnt = 1; //阶段A长度1
chctl1_baudprediv = 1; //ctrl0_pdiv分频的基础上再进行2分频；
使能中断
ie_txie = 1; //使能发送FIFO中断
ie_rxie = 1; //使能接收FIFO中断
ie_errie = 9’h1ff; //使能各错误中断
使能SPI：
ctrl0_en = 1'b1;//SPI使能
向txfifo写入配置和数据(sconfpush和datpush0~datpush8不能通过原子操作进行写)：
sconfpush = 32’h0780_0001; //ss=0; datcnt=f; bytes=0; last=1;表示与从机spi_slso0通信，数据长度16 bits；短数据模式(bytes=0; last=1)；
datpush0 = 32’h0000_1234; //传输数据为1234；
与从机1通信：
sconfpush = 32’h17C0_0001; //ss=1; datcnt=f; bytes=1; last=1;表示与从机spi_slso0通信，数据长度16 Bytes；长数据模式(bytes=1; last=1)；
datpush0 = 32’h1234_5678; //传输数据为’h1234_5678；
datpush1 = 32’h9abc_def0; //传输数据为’h9abc_def0；
datpush2 = 32’h55aa_aa55; //传输数据为’h55aa_aa55；
datpush3 = 32’h33cc_cc33; //传输数据为’h33cc_cc33；
检测到rxfifo的接收中断if_rxif后，读RXFIFO；
mov r0 #0xF400 00AC//汇编
ld.w  r1  [r0] //汇编
从机模式
打开时钟：
clkc_disr = 0; //该步骤操作的前提是CPU处于SV模式，并且SCU配置为endinit阶段
配置ctl0寄存器：
ctrl0_clksel = 1;
ctrl0_mod = 2'b10; //从机模式
ctrl0_pdiv = 3; //对工作时钟分频：4分频
配置ctl1寄存器：
ctrl1_txmod = 1; //txfifo中断触发模式
ctrl1_rxmod = 1；//rxfifo中断触发模式
配置sscfg寄存器：
sscfg_ssen = 16’h0000; //不使能从机选择信号；
sscfg_sslevel =16’hffff; //从机不使能时片选信号为全1；
配置portsel寄存器：
portsel_slsis = 3’d1;//从机选择片选信号输入端口1：spi_slsi1；
portsel_scis = 3’d0;//从机选择时钟输入端口1：spi_sclk1
portsel_sris = 3’d0; //从机选择数据输入端口1：spi_mtsr1
与spi_slso0、spi_slso8所挂载的从机进行传输时的特性，通过chctl0进行配置：
chctl0_bigend = 0；//小端模式
chctl0_parcheck = 0； //禁用奇偶校验
chctl0_sckpol = 0; //极性0
chctl0_sckphase = 1; //相位1
chctl0_ccnt = 1； //阶段C长度1
chctl0_bcnt =0；  //阶段B长度0
chctl0_acnt = 1; //阶段A长度1
chctl0_baudprediv = 3; //ctrl0_pdiv分频的基础上再进行4分频；
与spi_slso1、spi_slso9所挂载的从机进行传输时的特性，通过chctl1进行配置：
chctl1_bigend = 0；//小端模式
chctl1_parcheck = 1； //禁用奇偶校验
chctl1_sckpol = 1; //极性0
chctl1_sckphase = 1; //相位1
chctl1_ccnt = 1； //阶段C长度1
chctl1_bcnt =0；  //阶段B长度0
chctl1_acnt = 1; //阶段A长度1
chctl1_baudprediv = 1; //ctrl0_pdiv分频的基础上再进行2分频；
使能中断
ie_txie = 1; //使能发送FIFO中断
ie_rxie = 1; //使能接收FIFO中断
ie_errie = 9’h1ff; //使能各错误中断
使能SPI：
ctrl0_en = 1'b1;//SPI使能
向txfifo写入配置和数据(sconfpush和datpush0~datpush8不能通过原子操作进行写)：
sconfpush = 32’h0780_0001; //ss=0; datcnt=f; bytes=0; last=1;表示与主机spi_slsi1通信，数据长度16 bits；短数据模式(bytes=0; last=1)；
datpush0 = 32’h0000_1234; //传输数据为1234；
检测到rxfifo的接收中断if_rxif后，读RXFIFO；
mov r0 #0xF400 00AC//汇编
ld.w  r1  [r0] //汇编
接口描述
接口信号
方向
描述
spi_mrst1
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst2
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst3
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst4
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst5
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst6
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst7
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst8
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst9
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst10
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst11
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst12
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst13
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst14
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst15
I
主机模式，SPI数据输入线，来自GPIO；
spi_mrst16
I
主机模式，SPI数据输入线，来自GPIO；
spi_sclk
O
主机模式，SPI时钟输出线；连接到GPIO；
spi_slso0
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso1
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso2
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso3
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso4
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso5
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso6
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso7
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso8
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso9
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso10
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso11
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso12
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso13
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso14
O
主机模式，SPI片选信号线；连接到GPIO；
spi_slso15
O
主机模式，SPI片选信号线；连接到GPIO；
spi_mtsr
O
主机模式，SPI数据输出线；连接到GPIO；
spi_slsi1
I
从机模式，SPI片选信号线，来自GPIO；
spi_slsi2
I
从机模式，SPI片选信号线，来自GPIO；
spi_slsi3
I
从机模式，SPI片选信号线，来自GPIO；
spi_slsi4
I
从机模式，SPI片选信号线，来自GPIO；
spi_slsi5
I
从机模式，SPI片选信号线，来自GPIO；
spi_slsi6
I
从机模式，SPI片选信号线，来自GPIO；
spi_slsi7
I
从机模式，SPI片选信号线，来自GPIO；
spi_sclk1
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk2
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk3
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk4
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk5
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk6
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk7
I
从机模式，SPI时钟输入线，来自GPIO；
spi_sclk8
I
从机模式，SPI时钟输入线，来自GPIO；
spi_mtsr1
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr2
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr3
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr4
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr5
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr6
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr7
I
从机模式，SPI数据输入线，来自GPIO；
spi_mtsr8
I
从机模式，SPI数据输入线，来自GPIO；
spi_mrst
O
从机模式，SPI数据输出线；连接到GPIO；
intreq_spi0tx
O
发送中断请求线，连接到中断路由模块IR；
intreq_spi0rx
O
接收中断请求线，连接到中断路由模块IR；
intreq_spi0err
O
错误中断请求线，连接到中断路由模块IR；
intreq_spi0pt
O
传输阶段中断请求线，连接到中断路由模块IR；
intreq_spi0u
O
用户中断请求线，连接到中断路由模块IR；
spi_si
O
由spi_mtsr1~spi_mtsr8经过PORTSEL_SRIS位8选一之后得到，连接到外部请求单元ERU；
spi_sck
O
由spi_sck1~spi_sck8经过PORTSEL_SCIS位8选一之后得到，连接到外部请求单元ERU；
spi_mi
O
由spi_mrst1~spi_mrst16经过PORTSEL_MRIS位16选一之后得到，连接到外部请求单元ERU；
spi_ss
O
由spi_slsi1~spi_slsi7经过PORTSEL_SLSIS位7选一之后得到，连接到外部请求单元ERU；
版本更新记录
版本号
描述
时间
V0.1
初版
2023/04/14
V0.2
修改基地址；修改INFO寄存器；寄存器列表中增加复位源列
2023/10/25
V0.3
添加寄存器PORTSEL；
修改寄存器偏移地址，之前从寄存器SPIx_CHCTLi之后排列错误；
2024/3/6
V0.4
更新寄存器SPIx_CTL1_TXMOD/RXMOD;
2024/3/12
V0.5
更新寄存器MRIS
2024/4/22
V0.6
加入IS寄存器和TM寄存器；
修改RXPOP寄存器的复位值；
修改MIXPUSH/SCTLPUSH/DATPUSH寄存器读写权限
2024/5/30
V0.7
修改寄存器基地址
2024/08/06
V0.8
添加接口章节；添加典型使用场景；
2024/09/06
V0.9
修改BIGEND寄存器位的描述
2024/10/10
V1.0
修改SPI_IF的复位值为0x0000 0020；
修改寄存器：SPIx_CTL1_RXMOD、SPIx_CTL1_TXMOD；
修改章节描述1.4.7.2 TXFIFO中断的生成、1.4.7.3 RXFIFO中断的生成
完善SPIx_TM寄存器；
2024/11/15
V1.1
修改SPI_IF的复位值为0x0000 0200；
2024/11/18
V1.2
修改SPI_CTL0_CLR的属性为RWH；
修改1.4.7章节中断框图；
2025/1/2
V1.3
修改ACES1寄存器的描述；
修改TM_TMSEL寄存器；
增加TXFIFO写入规则的描述；
2025/1/17
V1.4
增加描述：只有短数据模式支持奇偶校验；
新增寄存器：SPIx_INTM；
修改章节1.4.7 中断；
2025/3/21
V1.5
修改CHCTLi_BAUDPREDIV：0~64改成1~64；
2025/4/1
V1.6
修改TRANSPHA：增加9(Stop阶段)；
修改“FIFO功能”章节：补充SCTL-DATA PUSH和MIX PUSH不能混用的说明，以及MIX PUSH的使用注意事项；
增加slave的三线模式描述；
增加配置报错条件的描述。
2025/4/7
V1.7
更新STAINJ的描述
修改1.4.3.1：从机模式下支持各种极性、相位，但有条件；
修改1.4.2.5：从机模式下，波特率公式的分母至少为5；
2025/4/28
V1.8
更新SPIx_CHCTLi.ACNT位域描述
2026/5/6
附录：寄存器访问权限
寄存器总表要求包括各寄存器偏移地址、寄存器名、访问权限、简单功能表述以及复位值。
访问权限分为读权限和写权限，权限内容包括：
表 21 寄存器访问权限表
符号
描述
BER
对该寄存器的写操作会触发BUS ERROR
CPUx
只能通过CPUx来访问
CEx
只有在CPUxWDT的ENDINIT位置零时才可以访问
ALE
任意CPUWDT的ENDINIT位置零或者全局ENDINIT置零时可以访问
HSM
只能通过HSM来访问
MOD
模块特定访问条件，该条件在模块规格书中有详细描述
OCEN
只有在OCDS使能时才可以访问
P
由ACCEN0寄存器指定的MASTER可以访问
P0
由ACCEN00寄存器指定的MASTER可以访问
P1
由ACCEN10寄存器指定的MASTER可以访问
Pr
由ACCENr0或ACCENr1指定的MASTER可以访问
P00/P01
由ACCEN00/01寄存器指定的MASTER可以访问
PAS
只有在提供正确密码的前提下可以访问
SE
只有当安全ENDINIT位置零时可以访问
SU
只能在启动阶段由SSW访问
SV
只有在管理员模式下访问
TEST
只有在SPI处于测试模式下可以访问
USER/U
只有在用户模式下可以访问
32
只有当数据宽度为32bit时可以访问
32,64
只有在数据宽度为32bit或64bit时可以访问