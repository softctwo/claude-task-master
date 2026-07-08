import { execa, type Result } from "execa";
import fs from "fs-extra";
import path from "path";
import { globby } from "globby";

import type {
  TaskmasterProject,
  TaskmasterTask,
} from "@resoft/types";

export interface AdapterOptions {
  taskmasterPath: string;
  projectPath: string;
  modelConfig?: {
    provider?: string;
    model?: string;
    apiKey?: string;
  };
  /** CLI 调用超时（毫秒），默认 60000 */
  timeout?: number;
  /** 最大重试次数，默认 3 */
  maxRetries?: number;
  /** 是否启用日志 */
  enableLogging?: boolean;
}

interface LogEntry {
  timestamp: string;
  level: "info" | "warn" | "error" | "debug";
  action: string;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Taskmaster Adapter - 封装 CLI/MCP 调用
 * 提供稳定接口，避免业务层直接依赖 CLI 字符串
 * 包含错误重试、超时控制和结构化日志
 */
export class TaskmasterAdapter {
  private options: Required<AdapterOptions>;
  private logs: LogEntry[] = [];

  constructor(options: AdapterOptions) {
    this.options = {
      taskmasterPath: options.taskmasterPath,
      projectPath: options.projectPath,
      modelConfig: options.modelConfig || {},
      timeout: options.timeout ?? 60000,
      maxRetries: options.maxRetries ?? 3,
      enableLogging: options.enableLogging ?? true,
    };
  }

  // ---- 日志系统 ----

  private log(level: LogEntry["level"], action: string, message: string, details?: Record<string, unknown>): void {
    if (!this.options.enableLogging) return;
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      action,
      message,
      details,
    };
    this.logs.push(entry);
    // 控制台输出
    const prefix = `[${entry.timestamp}] [${level.toUpperCase()}] [${action}]`;
    if (level === "error") {
      console.error(prefix, message);
    } else if (level === "warn") {
      console.warn(prefix, message);
    } else {
      console.log(prefix, message);
    }
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs(): void {
    this.logs = [];
  }

  async saveLogs(logPath?: string): Promise<void> {
    const targetPath = logPath || path.join(this.options.projectPath, ".taskmaster", "adapter-logs.json");
    await fs.ensureDir(path.dirname(targetPath));
    await fs.writeJson(targetPath, this.logs, { spaces: 2 });
  }

  // ---- 核心执行方法（带重试和超时） ----

  private async execWithRetry(
    command: string,
    args: string[],
    options: { cwd: string; timeout: number }
  ): Promise<Result> {
    const maxRetries = this.options.maxRetries;
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      this.log("debug", "exec", `执行命令 (尝试 ${attempt}/${maxRetries}): ${command} ${args.join(" ")}`);

      try {
        const result = await execa(command, args, {
          cwd: options.cwd,
          timeout: options.timeout,
          reject: true,
          env: this.buildEnv(),
        });
        this.log("info", "exec", `命令执行成功`, {
          command: `${command} ${args.join(" ")}`,
          exitCode: result.exitCode,
          stdoutPreview: result.stdout?.slice(0, 200),
        });
        return result;
      } catch (error: any) {
        lastError = error;
        const isTimeout = error.message?.includes("timed out") || error.exitCode === null;
        const isCliNotFound = error.exitCode === 127 || error.message?.includes("ENOENT");

        this.log("warn", "exec", `命令执行失败 (尝试 ${attempt}/${maxRetries})`, {
          command: `${command} ${args.join(" ")}`,
          error: error.message,
          exitCode: error.exitCode,
          isTimeout,
          isCliNotFound,
        });

        // 如果是 CLI 未找到，直接失败不重试
        if (isCliNotFound) {
          throw new Error(
            `task-master CLI 未找到。请确保已安装: npm install -g task-master\n原始错误: ${error.message}`
          );
        }

        // 最后一次尝试，抛出错误
        if (attempt === maxRetries) {
          break;
        }

        // 指数退避重试
        const delayMs = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
        this.log("debug", "exec", `等待 ${delayMs}ms 后重试...`);
        await this.sleep(delayMs);
      }
    }

    throw new Error(
      `命令执行失败 (${maxRetries} 次尝试后): ${command} ${args.join(" ")}\n错误: ${lastError?.message || "Unknown error"}`
    );
  }

  private buildEnv(): Record<string, string | undefined> {
    const env: Record<string, string | undefined> = { ...process.env };
    if (this.options.modelConfig.provider) {
      env.MODEL_PROVIDER = this.options.modelConfig.provider;
    }
    if (this.options.modelConfig.model) {
      env.MODEL_NAME = this.options.modelConfig.model;
    }
    if (this.options.modelConfig.apiKey) {
      env.API_KEY = this.options.modelConfig.apiKey;
    }
    return env;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ---- 验证 CLI 可用性 ----

  async validateCli(): Promise<{ available: boolean; version?: string; error?: string }> {
    try {
      const { stdout } = await execa("task-master", ["--version"], {
        cwd: this.options.projectPath,
        timeout: 10000,
        reject: false,
      });
      if (stdout && stdout.includes("task-master")) {
        this.log("info", "validate", `task-master CLI 可用: ${stdout.trim()}`);
        return { available: true, version: stdout.trim() };
      }
      return { available: false, error: "无法获取版本信息" };
    } catch (error: any) {
      this.log("error", "validate", `task-master CLI 不可用: ${error.message}`);
      return { available: false, error: error.message };
    }
  }

  // ---- 公共方法 ----

  /**
   * 初始化项目级 Taskmaster 工作目录
   */
  async initProject(): Promise<{ success: boolean; message: string }> {
    this.log("info", "initProject", "开始初始化 Taskmaster 项目");
    try {
      await this.execWithRetry("task-master", ["init"], {
        cwd: this.options.projectPath,
        timeout: this.options.timeout,
      });
      this.log("info", "initProject", "Taskmaster 项目初始化成功");
      return { success: true, message: "Taskmaster 项目初始化成功" };
    } catch (error: any) {
      this.log("error", "initProject", `初始化失败: ${error.message}`);
      return {
        success: false,
        message: `初始化失败: ${error.message}`,
      };
    }
  }

  /**
   * 从 PRD 解析生成任务
   */
  async parsePrd(prdPath: string): Promise<{
    success: boolean;
    tasks: TaskmasterTask[];
    message?: string;
  }> {
    this.log("info", "parsePrd", `开始解析 PRD: ${prdPath}`);
    try {
      await this.execWithRetry("task-master", ["parse-prd", prdPath], {
        cwd: this.options.projectPath,
        timeout: this.options.timeout,
      });

      const tasks = await this.readTasks();
      this.log("info", "parsePrd", `PRD 解析成功，读取到 ${tasks.length} 个任务`);
      return { success: true, tasks };
    } catch (error: any) {
      this.log("error", "parsePrd", `解析 PRD 失败: ${error.message}`);
      return {
        success: false,
        tasks: [],
        message: `解析 PRD 失败: ${error.message}`,
      };
    }
  }

  /**
   * 拆解任务
   */
  async expandTask(taskId: string): Promise<{
    success: boolean;
    subtasks: TaskmasterTask[];
    message?: string;
  }> {
    this.log("info", "expandTask", `开始拆解任务: ${taskId}`);
    try {
      await this.execWithRetry("task-master", ["expand", "--id", taskId], {
        cwd: this.options.projectPath,
        timeout: this.options.timeout,
      });

      const tasks = await this.readTasks();
      const task = this.findTaskById(tasks, taskId);
      this.log("info", "expandTask", `任务拆解完成，${task?.subtasks?.length || 0} 个子任务`);
      return { success: true, subtasks: task?.subtasks || [] };
    } catch (error: any) {
      this.log("error", "expandTask", `拆解任务失败: ${error.message}`);
      return {
        success: false,
        subtasks: [],
        message: `拆解任务失败: ${error.message}`,
      };
    }
  }

  /**
   * 分析任务复杂度
   */
  async analyzeComplexity(): Promise<{
    success: boolean;
    report?: string;
    message?: string;
  }> {
    this.log("info", "analyzeComplexity", "开始分析任务复杂度");
    try {
      await this.execWithRetry("task-master", ["analyze-complexity"], {
        cwd: this.options.projectPath,
        timeout: this.options.timeout,
      });

      // 读取复杂度报告
      const reportsDir = path.join(
        this.options.projectPath,
        ".taskmaster",
        "reports"
      );
      const reportFiles = await globby("*.md", { cwd: reportsDir });
      const report = reportFiles.length > 0
        ? await fs.readFile(path.join(reportsDir, reportFiles[0]), "utf-8")
        : undefined;

      this.log("info", "analyzeComplexity", `复杂度分析完成，报告文件: ${reportFiles.length > 0 ? reportFiles[0] : "无"}`);
      return { success: true, report };
    } catch (error: any) {
      this.log("error", "analyzeComplexity", `复杂度分析失败: ${error.message}`);
      return {
        success: false,
        message: `复杂度分析失败: ${error.message}`,
      };
    }
  }

  /**
   * 获取推荐下一个任务
   */
  async getNextTask(): Promise<{
    success: boolean;
    task?: TaskmasterTask;
    message?: string;
  }> {
    this.log("info", "getNextTask", "获取推荐任务");
    try {
      const { stdout } = await this.execWithRetry("task-master", ["next"], {
        cwd: this.options.projectPath,
        timeout: this.options.timeout,
      });

      const tasks = await this.readTasks();
      // 解析 stdout 中的任务 ID
      const taskIdMatch = stdout.match(/task[_-]?([a-zA-Z0-9]+)/i);
      if (taskIdMatch) {
        const taskId = taskIdMatch[1];
        const task = this.findTaskById(tasks, taskId);
        this.log("info", "getNextTask", `推荐任务: ${task?.title || taskId}`);
        return { success: true, task };
      }

      this.log("info", "getNextTask", `未在输出中解析到任务 ID，返回原始输出`);
      return { success: true, message: stdout };
    } catch (error: any) {
      this.log("error", "getNextTask", `获取 next task 失败: ${error.message}`);
      return {
        success: false,
        message: `获取 next task 失败: ${error.message}`,
      };
    }
  }

  /**
   * 更新任务状态
   */
  async setTaskStatus(
    taskId: string,
    status: string
  ): Promise<{ success: boolean; message: string }> {
    this.log("info", "setTaskStatus", `更新任务状态: ${taskId} -> ${status}`);
    try {
      await this.execWithRetry(
        "task-master",
        ["set-status", "--id", taskId, "--status", status],
        {
          cwd: this.options.projectPath,
          timeout: this.options.timeout,
        }
      );
      this.log("info", "setTaskStatus", `任务 ${taskId} 状态已更新为 ${status}`);
      return { success: true, message: `任务 ${taskId} 状态已更新为 ${status}` };
    } catch (error: any) {
      this.log("error", "setTaskStatus", `更新任务状态失败: ${error.message}`);
      return {
        success: false,
        message: `更新任务状态失败: ${error.message}`,
      };
    }
  }

  /**
   * 从 Taskmaster 同步任务数据到数据库
   */
  async syncFromTaskmaster(): Promise<{
    success: boolean;
    project: TaskmasterProject;
    message?: string;
  }> {
    this.log("info", "syncFromTaskmaster", "从 Taskmaster 同步数据");
    try {
      const tasks = await this.readTasks();
      const dependencies = await this.readDependencies();
      this.log("info", "syncFromTaskmaster", `同步完成，${tasks.length} 个任务`);
      return { success: true, project: { tasks, dependencies } };
    } catch (error: any) {
      this.log("error", "syncFromTaskmaster", `同步失败: ${error.message}`);
      return {
        success: false,
        project: { tasks: [], dependencies: {} },
        message: `同步失败: ${error.message}`,
      };
    }
  }

  /**
   * 将数据库任务数据同步到 Taskmaster
   */
  async syncToTaskmaster(
    project: TaskmasterProject
  ): Promise<{ success: boolean; message: string }> {
    this.log("info", "syncToTaskmaster", `同步 ${project.tasks.length} 个任务到 Taskmaster`);
    try {
      const tasksPath = path.join(
        this.options.projectPath,
        ".taskmaster",
        "tasks"
      );
      await fs.ensureDir(tasksPath);

      // 写入任务文件
      for (const task of project.tasks) {
        const taskFile = path.join(tasksPath, `${task.id}.json`);
        await fs.writeJson(taskFile, task, { spaces: 2 });
      }

      // 写入依赖关系
      if (Object.keys(project.dependencies).length > 0) {
        const depsPath = path.join(
          this.options.projectPath,
          ".taskmaster",
          "dependencies.json"
        );
        await fs.writeJson(depsPath, project.dependencies, { spaces: 2 });
      }

      this.log("info", "syncToTaskmaster", "任务数据已同步到 Taskmaster");
      return { success: true, message: "任务数据已同步到 Taskmaster" };
    } catch (error: any) {
      this.log("error", "syncToTaskmaster", `同步到 Taskmaster 失败: ${error.message}`);
      return {
        success: false,
        message: `同步到 Taskmaster 失败: ${error.message}`,
      };
    }
  }

  /**
   * 运行研究任务
   */
  async runResearch(query: string): Promise<{
    success: boolean;
    result?: string;
    message?: string;
  }> {
    this.log("info", "runResearch", `运行研究任务: ${query}`);
    try {
      const { stdout } = await this.execWithRetry("task-master", ["research", query], {
        cwd: this.options.projectPath,
        timeout: this.options.timeout,
      });
      this.log("info", "runResearch", "研究任务完成");
      return { success: true, result: stdout };
    } catch (error: any) {
      this.log("error", "runResearch", `研究任务失败: ${error.message}`);
      return {
        success: false,
        message: `研究任务失败: ${error.message}`,
      };
    }
  }

  /**
   * 列出所有任务
   */
  async listTasks(): Promise<{
    success: boolean;
    tasks: TaskmasterTask[];
    message?: string;
  }> {
    this.log("info", "listTasks", "列出所有任务");
    try {
      const tasks = await this.readTasks();
      this.log("info", "listTasks", `找到 ${tasks.length} 个任务`);
      return { success: true, tasks };
    } catch (error: any) {
      this.log("error", "listTasks", `列出任务失败: ${error.message}`);
      return {
        success: false,
        tasks: [],
        message: `列出任务失败: ${error.message}`,
      };
    }
  }

  /**
   * 获取任务详情
   */
  async getTask(taskId: string): Promise<{
    success: boolean;
    task?: TaskmasterTask;
    message?: string;
  }> {
    this.log("info", "getTask", `获取任务详情: ${taskId}`);
    try {
      const tasks = await this.readTasks();
      const task = this.findTaskById(tasks, taskId);
      if (task) {
        this.log("info", "getTask", `找到任务: ${task.title}`);
        return { success: true, task };
      }
      this.log("warn", "getTask", `任务未找到: ${taskId}`);
      return { success: false, message: `任务未找到: ${taskId}` };
    } catch (error: any) {
      this.log("error", "getTask", `获取任务失败: ${error.message}`);
      return {
        success: false,
        message: `获取任务失败: ${error.message}`,
      };
    }
  }

  // ---- 私有方法 ----

  private async readTasks(): Promise<TaskmasterTask[]> {
    const tasksDir = path.join(
      this.options.projectPath,
      ".taskmaster",
      "tasks"
    );

    if (!(await fs.pathExists(tasksDir))) {
      return [];
    }

    const files = await globby("*.json", { cwd: tasksDir });
    const tasks: TaskmasterTask[] = [];

    for (const file of files) {
      try {
        const task = await fs.readJson(path.join(tasksDir, file));
        tasks.push(task);
      } catch (error: any) {
        this.log("warn", "readTasks", `读取任务文件失败: ${file} - ${error.message}`);
      }
    }

    return tasks;
  }

  private async readDependencies(): Promise<Record<string, string[]>> {
    const depsPath = path.join(
      this.options.projectPath,
      ".taskmaster",
      "dependencies.json"
    );

    if (await fs.pathExists(depsPath)) {
      try {
        return await fs.readJson(depsPath);
      } catch (error: any) {
        this.log("warn", "readDependencies", `读取依赖文件失败: ${error.message}`);
      }
    }

    return {};
  }

  private findTaskById(
    tasks: TaskmasterTask[],
    taskId: string
  ): TaskmasterTask | undefined {
    for (const task of tasks) {
      if (task.id === taskId) return task;
      if (task.subtasks) {
        const found = this.findTaskById(task.subtasks, taskId);
        if (found) return found;
      }
    }
    return undefined;
  }
}

export default TaskmasterAdapter;
