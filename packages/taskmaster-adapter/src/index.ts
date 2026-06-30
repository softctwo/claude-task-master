import { execa } from "execa";
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
}

/**
 * Taskmaster Adapter - 封装 CLI/MCP 调用
 * 提供稳定接口，避免业务层直接依赖 CLI 字符串
 */
export class TaskmasterAdapter {
  private options: AdapterOptions;

  constructor(options: AdapterOptions) {
    this.options = options;
  }

  /**
   * 初始化项目级 Taskmaster 工作目录
   */
  async initProject(): Promise<{ success: boolean; message: string }> {
    try {
      await execa("task-master", ["init"], {
        cwd: this.options.projectPath,
      });
      return { success: true, message: "Taskmaster 项目初始化成功" };
    } catch (error) {
      return {
        success: false,
        message: `初始化失败: ${error}`,
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
    try {
      await execa("task-master", ["parse-prd", prdPath], {
        cwd: this.options.projectPath,
      });

      const tasks = await this.readTasks();
      return { success: true, tasks };
    } catch (error) {
      return {
        success: false,
        tasks: [],
        message: `解析 PRD 失败: ${error}`,
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
    try {
      await execa("task-master", ["expand", "--id", taskId], {
        cwd: this.options.projectPath,
      });

      const tasks = await this.readTasks();
      const task = this.findTaskById(tasks, taskId);
      return { success: true, subtasks: task?.subtasks || [] };
    } catch (error) {
      return {
        success: false,
        subtasks: [],
        message: `拆解任务失败: ${error}`,
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
    try {
      await execa("task-master", ["analyze-complexity"], {
        cwd: this.options.projectPath,
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

      return { success: true, report };
    } catch (error) {
      return {
        success: false,
        message: `复杂度分析失败: ${error}`,
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
    try {
      const { stdout } = await execa("task-master", ["next"], {
        cwd: this.options.projectPath,
      });

      const tasks = await this.readTasks();
      // 解析 stdout 中的任务 ID
      const taskIdMatch = stdout.match(/task[_-]?([a-zA-Z0-9]+)/i);
      if (taskIdMatch) {
        const taskId = taskIdMatch[1];
        const task = this.findTaskById(tasks, taskId);
        return { success: true, task };
      }

      return { success: true, message: stdout };
    } catch (error) {
      return {
        success: false,
        message: `获取 next task 失败: ${error}`,
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
    try {
      await execa("task-master", ["set-status", "--id", taskId, "--status", status], {
        cwd: this.options.projectPath,
      });
      return { success: true, message: `任务 ${taskId} 状态已更新为 ${status}` };
    } catch (error) {
      return {
        success: false,
        message: `更新任务状态失败: ${error}`,
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
    try {
      const tasks = await this.readTasks();
      const dependencies = await this.readDependencies();
      return { success: true, project: { tasks, dependencies } };
    } catch (error) {
      return {
        success: false,
        project: { tasks: [], dependencies: {} },
        message: `同步失败: ${error}`,
      };
    }
  }

  /**
   * 将数据库任务数据同步到 Taskmaster
   */
  async syncToTaskmaster(
    project: TaskmasterProject
  ): Promise<{ success: boolean; message: string }> {
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

      return { success: true, message: "任务数据已同步到 Taskmaster" };
    } catch (error) {
      return {
        success: false,
        message: `同步到 Taskmaster 失败: ${error}`,
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
    try {
      const { stdout } = await execa("task-master", ["research", query], {
        cwd: this.options.projectPath,
      });
      return { success: true, result: stdout };
    } catch (error) {
      return {
        success: false,
        message: `研究任务失败: ${error}`,
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
      const task = await fs.readJson(path.join(tasksDir, file));
      tasks.push(task);
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
      return await fs.readJson(depsPath);
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
