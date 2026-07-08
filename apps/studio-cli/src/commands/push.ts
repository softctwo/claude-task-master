import chalk from "chalk";
import ora from "ora";
import fs from "fs-extra";
import path from "path";
import { getApiClient, getCurrentProjectId } from "./api-client.js";

const TASKMASTER_DIR = ".taskmaster";

export async function push(options: { tasks?: boolean }) {
  const projectId = await getCurrentProjectId();
  if (!projectId) {
    console.error(chalk.red("❌ 未选择项目。请先运行: resoft-studio init <project-id>"));
    process.exit(1);
  }

  console.log(chalk.blue(`⬆️ 推送本地变更到平台 (项目: ${projectId})`));
  const client = await getApiClient();

  // 如果没有指定选项，默认推送任务
  const pushTasks = options.tasks || !options.tasks;

  if (pushTasks) {
    const spinner = ora("推送任务状态变更...").start();
    try {
      const tasksDir = path.join(TASKMASTER_DIR, "tasks");
      if (!(await fs.pathExists(tasksDir))) {
        spinner.warn("本地任务目录不存在，跳过");
        console.log(chalk.green("✅ 推送完成"));
        return;
      }

      const files = await fs.readdir(tasksDir);
      let pushedCount = 0;
      let skippedCount = 0;

      for (const file of files) {
        if (!file.endsWith(".json")) continue;

        const task = await fs.readJson(path.join(tasksDir, file));
        const resoftMeta = task._resoft_meta || {};
        const taskId = resoftMeta.task_id;

        if (!taskId) {
          // 尝试通过 taskmaster_task_id 查找
          try {
            const { data: existing } = await client.get("/tasks", {
              params: {
                project_id: projectId,
                page_size: 100,
              },
            });
            const match = existing.items?.find((t: any) =>
              t.taskmaster_task_id === task.id || t.title === task.title
            );
            if (match) {
              await client.put(`/tasks/${match.task_id}`, {
                status: task.status,
                priority: task.priority,
                title: task.title,
                description: task.description,
              });
              pushedCount++;
            } else {
              // 创建新任务
              await client.post("/tasks", {
                project_id: projectId,
                title: task.title,
                description: task.description,
                details: task.details,
                priority: task.priority || "medium",
                status: task.status || "pending",
                taskmaster_task_id: task.id,
                dependencies: task.dependencies || [],
              });
              pushedCount++;
            }
          } catch (err: any) {
            skippedCount++;
            // 继续处理其他任务
          }
        } else {
          // 更新已有任务
          try {
            await client.put(`/tasks/${taskId}`, {
              status: task.status,
              priority: task.priority,
              title: task.title,
              description: task.description,
              details: task.details,
            });
            pushedCount++;
          } catch (err: any) {
            skippedCount++;
          }
        }
      }

      spinner.succeed(`已推送 ${pushedCount} 个任务${skippedCount > 0 ? `, ${skippedCount} 个跳过` : ""}`);
    } catch (error: any) {
      spinner.fail(`推送失败: ${error.message || String(error)}`);
      process.exit(1);
    }
  }

  console.log(chalk.green("✅ 推送完成"));
}
