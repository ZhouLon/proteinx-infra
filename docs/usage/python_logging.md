# Python 日志模块

## 日志模块的作用

logging模块是Python的标准库的一部分，它使得追踪事件、诊断问题和调试应用程序变得容易。它提供了不同的日志级别，如DEBUG、INFO、WARNING、ERROR和CRITICAL，这可以帮助开发者根据重要性区分日志消息。

| 组件 | 描述 |
|------|------|
| Logger | 日志记录器，提供了应用程序可直接使用的接口来记录消息。 |
| Handler | 处理器负责将日志记录（由Logger创建）发送到合适的目的地。 |
| Formatter | 格式化器决定日志记录的最终输出格式。 |
| Filter | 过滤器提供了更细粒度的工具来确定输出哪些日志记录。 |
| LogRecord | 日志记录对象，包含了所有日志信息的数据结构。 |
| Level | 日志级别如DEBUG、INFO、WARNING、ERROR和CRITICAL，用于区分消息的严重性。 |

级别值: DEBUG < INFO < WARNING < ERROR < CRITICAL，值越大表示日志级别越高。DEBUG: 10、INFO: 20、WARNING: 30、ERROR: 40、CRITICAL: 50
注：级别的数值表明了它们的优先级：数值更低的级别表示更详细的、经常是用于调试目的的信息，而数值更高的级别表示更严重的情况。当你设置一个日志记录器（Logger）的级别时，它会记录该级别以及比该级别更高级别的所有日志消息。例如，如果设置日志级别为INFO，则记录器会记录INFO, WARNING, ERROR和CRITICAL级别的消息，而忽略DEBUG级别的消息。


## Formatter 格式属性

| 属性 | 格式 | 描述 |
|------|------|------|
| asctime | %(asctime)s | 日志产生的时间，默认格式为 2003-07-08 16:49:45,896 |
| msecs | %(msecs)d | 日志生成时间的毫秒部分 |
| created | %(created)f | time.time() 生成的日志创建时间戳 |
| message | %(message)s | 具体的日志信息内容 |
| filename | %(filename)s | 生成日志的程序名 |
| name | %(name)s | 日志调用者 |
| funcName | %(funcName)s | 调用日志的函数名 |
| levelname | %(levelname)s | 日志级别(DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| levelno | %(levelno)s | 日志级别对应的数值 |
| lineno | %(lineno)d | 日志所针对的代码行号（如果可用的话） |
| module | %(module)s | 生成日志的模块名 |
| pathname | %(pathname)s | 生成日志的文件的完整路径 |
| process | %(process)d | 生成日志的进程ID（如果可用） |
| processName | %(processName)s | 进程名（如果可用） |
| thread | %(thread)d | 生成日志的线程ID（如果可用） |
| threadName | %(threadName)s | 线程名（如果可用） |
| exc_info | %(exc_info)s | 如果日志消息由异常触发，则包括异常信息 |
| relativeCreated | %(relativeCreated)d | 日志消息被创建的时间（以毫秒为单位），相对于 Logger 对象被创建的时间 |
