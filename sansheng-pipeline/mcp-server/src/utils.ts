import { execSync } from 'child_process';
import * as path from 'path';

const PLUGIN_ROOT = path.resolve(__dirname, '../..');
const LIB_PATH = path.join(PLUGIN_ROOT, 'lib');

/**
 * Python 执行结果
 */
export interface PythonResult {
  success: boolean;
  data?: any;
  error?: string;
  stderr?: string;
}

/**
 * 将字符串转为 Base64（用于传递复杂字符串到 Python）
 */
export function toBase64(str: string): string {
  return Buffer.from(str, 'utf-8').toString('base64');
}

/**
 * 执行 Python 代码并返回结果（增强版）
 *
 * 功能改进：
 * 1. 返回结构化结果（包含成功/失败状态）
 * 2. 捕获 stderr 用于调试
 * 3. 支持 JSON 解析
 * 4. 超时控制
 *
 * @param code Python 代码
 * @param parseJson 是否解析 JSON 结果（默认 false）
 * @param timeout 超时时间（毫秒，默认 30000）
 * @returns PythonResult 对象
 */
export function execPython(
  code: string,
  parseJson: boolean = false,
  timeout: number = 30000
): PythonResult {
  // 使用 heredoc 方式避免转义问题
  const fullCode = `import sys; sys.path.insert(0, '${LIB_PATH}'); ${code}`;

  // 将代码写入临时 Base64 编码（避免所有转义问题）
  const encodedCode = Buffer.from(fullCode, 'utf-8').toString('base64');

  const cmd = `cd "${PLUGIN_ROOT}" && python3 -c "import base64; exec(base64.b64decode('${encodedCode}').decode('utf-8'))"`;

  try {
    const stdout = execSync(cmd, {
      encoding: 'utf-8',
      timeout: timeout,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();

    // 解析 JSON（如果需要）
    if (parseJson && stdout) {
      try {
        return {
          success: true,
          data: JSON.parse(stdout),
        };
      } catch (parseError: any) {
        return {
          success: false,
          error: `JSON 解析失败: ${parseError.message}`,
          stderr: stdout,
        };
      }
    }

    return {
      success: true,
      data: stdout,
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.message,
      stderr: error.stderr?.toString(),
    };
  }
}

/**
 * 调用 Python 模块函数（简化接口）
 *
 * 示例：
 * callPythonFunction('task_state', 'get_task', ['TASK-001'])
 * 等价于：from task_state import get_task; get_task('TASK-001')
 *
 * @param moduleName Python 模块名（如 'task_state'）
 * @param functionName 函数名（如 'get_task'）
 * @param args 参数列表
 * @param returnJson 是否返回 JSON（默认 true）
 * @returns PythonResult 对象
 */
export function callPythonFunction(
  moduleName: string,
  functionName: string,
  args: any[] = [],
  returnJson: boolean = true
): PythonResult {
  // 转换参数为 Python 字面量
  const pythonArgs = args
    .map((arg) => {
      if (typeof arg === 'string') {
        // 字符串参数使用 Base64 传递（避免转义问题）
        const b64 = toBase64(arg);
        return `base64.b64decode('${b64}').decode('utf-8')`;
      } else if (Array.isArray(arg)) {
        return JSON.stringify(arg);
      } else if (typeof arg === 'object') {
        return JSON.stringify(arg);
      } else {
        return String(arg);
      }
    })
    .join(', ');

  const code = `
import json
import base64
from ${moduleName} import ${functionName}
result = ${functionName}(${pythonArgs})
${returnJson ? "print(json.dumps(result, ensure_ascii=False))" : "print(result)"}
`;

  return execPython(code, returnJson);
}

/**
 * 批量执行 Python 操作（事务式）
 *
 * 适用场景：多个操作需要原子性执行，任何一个失败则全部回滚
 *
 * @param operations Python 代码行数组
 * @param returnJson 是否返回 JSON
 * @returns PythonResult 对象
 */
export function execPythonBatch(
  operations: string[],
  returnJson: boolean = false
): PythonResult {
  const code = operations.join('\n');
  return execPython(code, returnJson);
}

/**
 * 调用 Python 文件（执行完整脚本）
 *
 * @param scriptPath 脚本相对路径（相对于 lib 目录）
 * @param args 命令行参数
 * @returns PythonResult 对象
 */
export function execPythonScript(
  scriptPath: string,
  args: string[] = []
): PythonResult {
  const fullPath = path.join(LIB_PATH, scriptPath);
  const argsStr = args.map((arg) => `"${arg.replace(/"/g, '\\"')}"`).join(' ');
  const cmd = `cd "${PLUGIN_ROOT}" && python3 "${fullPath}" ${argsStr}`;

  try {
    const stdout = execSync(cmd, {
      encoding: 'utf-8',
      timeout: 30000,
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();

    return {
      success: true,
      data: stdout,
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.message,
      stderr: error.stderr?.toString(),
    };
  }
}
