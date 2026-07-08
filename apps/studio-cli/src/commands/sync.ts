import chalk from "chalk";
import ora from "ora";
import fs from "fs-extra";
import path from "path";
import { getApiClient, getCurrentProjectId } from "./api-client.js";

const TASKMASTER_DIR = ".taskmaster";
const RESOFT_DIR = ".resoft-studio";

export async function sync(options: { toRemote?: boolean; fromRemote?: boolean }) {
  const projectId = await getCurrentProjectId();
  if (!projectId) {
    console.error(chalk.red("❌ 未选择项目。请先运行: resoft-studio init <project-id>"));
    process.exit(1);
  }

  console.log(chalk.blue(`🔄 同步项目 ${projectId}`));
  const client = await getApiClient();

  if (options.toRemote) {
    const spinner = ora("推送到远程平台...").start();
    try {
      // 读取本地任务文件
      const tasksDir = path.join(TASKMASTER_DIR, "tasks");
      const localTasks: any[] = [];
      if (await fs.pathExists(tasksDir)) {
        const files = await fs.readdir(tasksDir);
        for (const file of files) {
          if (file.endsWith(".json")) {
            const task = await fs.readJson(path.join(tasksDir, file));
            localTasks.push(task);
          }
        }
      }

      // 推送任务到远程
      for (const task of localTasks) {
        try {
          await client.post("/tasks", {
            project_id: projectId,
            title: task.title || "Untitled",
            description: task.description,
            details: task.details,
            priority: mapPriority(task.priority),
            status: mapStatus(task.status),
            taskmaster_task_id: task.id,
            dependencies: task.dependencies || [],
          });
        } catch (err: any) {
          // 如果任务已存在，尝试更新
          if (err.message?.includes("409")) {
            // 尝试查找并更新
            try {
              const { data: existing } = await client.get("/tasks", {
                params: { project_id: projectId, page_size: 100 },
              });
              const match = existing.items?.find((t: any) => t.taskmaster_task_id === task.id);
              if (match) {
                await client.put(`/tasks/${match.task_id}`, {
                  title: task.title,
                  description: task.description,
                  status: mapStatus(task.status),
                  priority: mapPriority(task.priority),
                });
              }
            } catch (updateErr) {
              // 忽略更新错误
            }
          }
        }
      }

      // 更新同步状态
      const syncStatePath = path.join(RESOFT_DIR, "sync-state.json");
      await fs.writeJson(syncStatePath, {
        lastSyncAt: new Date().toISOString(),
        syncedTasks: localTasks.map((t) => t.id),
      });

      spinner.succeed(`已推送 ${localTasks.length} 个任务到远程`);
    } catch (error: any) {
      spinner.fail(`推送失败: ${error.message || String(error)}`);
      process.exit(1);
    }
  }

  if (options.fromRemote) {
    const spinner = ora("从远程平台拉取...").start();
    try {
      // 拉取任务
      const { data: tasksData } = await client.get("/tasks", {
        params: { project_id: projectId, page_size: 100 },
      });
      const tasks = tasksData.items || [];

      const tasksDir = path.join(TASKMASTER_DIR, "tasks");
      await fs.ensureDir(tasksDir);

      for (const task of tasks) {
        const taskFile = path.join(tasksDir, `${task.task_id}.json`);
        await fs.writeJson(taskFile, {
          id: task.taskmaster_task_id || task.task_id,
          title: task.title,
          description: task.description,
          details: task.details,
          status: task.status,
          priority: task.priority,
          complexity_score: task.complexity_score,
          dependencies: task.dependencies || [],
          _resoft_meta: {
            task_id: task.task_id,
            project_id: task.project_id,
            updated_at: task.updated_at,
          },
        }, { spaces: 2 });
      }

      // 拉取 Briefs
      const { data: briefsData } = await client.get("/briefs", {
        params: { project_id: projectId, page_size: 100 },
      });
      const briefs = briefsData.items || [];
      const briefsDir = path.join(RESOFT_DIR, "briefs");
      await fs.ensureDir(briefsDir);
      for (const brief of briefs) {
        const briefFile = path.join(briefsDir, `${brief.brief_id}.md`);
        let content = `# ${brief.title}\n\n`;
        if (brief.background) content += `## 背景\n\n${brief.background}\n\n`;
        if (brief.problem_statement) content += `## 问题陈述\n\n${brief.problem_statement}\n\n`;
        if (brief.target_users) content += `## 目标用户\n\n${brief.target_users}\n\n`;
        if (brief.goals?.length) content += `## 目标\n\n${brief.goals.map((g: string) => `- ${g}`).join("\n")}\n\n`;
        if (brief.acceptance_criteria?.length) {
          content += `## 验收标准\n\n${brief.acceptance_criteria.map((c: string) => `- ${c}`).join("\n")}\n\n`;
        }
        await fs.writeFile(briefFile, content);
      }

      // 拉取 PRDs
      const { data: prdsData } = await client.get("/prds", {
        params: { project_id: projectId, page_size: 100 },
      });
      const prds = prdsData.items || [];
      const prdsDir = path.join(RESOFT_DIR, "prds");
      await fs.ensureDir(prdsDir);
      for (const prd of prds) {
        const prdFile = path.join(prdsDir, `${prd.prd_id}.md`);
        await fs.writeFile(prdFile, prd.content_markdown || `# PRD ${prd.prd_id}\n\n`);
      }

      // 更新同步状态
      const syncStatePath = path.join(RESOFT_DIR, "sync-state.json");
      await fs.writeJson(syncStatePath, {
        lastSyncAt: new Date().toISOString(),
        syncedTasks: tasks.map((t: any) => t.task_id),
      });

      spinner.succeed(`已拉取 ${tasks.length} 个任务, ${briefs.length} 个 briefs, ${prds.length} 个 PRDs`);
    } catch (error: any) {
      spinner.fail(`拉取失败: ${error.message || String(error)}`);
      process.exit(1);
    }
  }

  if (!options.toRemote && !options.fromRemote) {
    console.log(chalk.yellow("⚠️ 请指定 --to-remote 或 --from-remote"));
    console.log(chalk.gray("  resoft-studio sync --to-remote    推送到远程"));
    console.log(chalk.gray("  resoft-studio sync --from-remote  从远程拉取"));
  }

  console.log(chalk.green("✅ 同步完成"));
}

function mapPriority(priority: string): string {
  const map: Record<string, string> = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low",
    p0: "critical",
    p1: "high",
    p2: "medium",
    p3: "low",
  };
  return map[priority?.toLowerCase()] || "medium";
}

function mapStatus(status: string): string {
  const map: Record<string, string> = {
    pending: "pending",
    "in_progress": "in_progress",
    done: "done",
    blocked: "blocked",
    deferred: "deferred",
    cancelled: "cancelled",
    todo: "pending",
    completed: "done",
    "in-progress": "in_progress",
  };
  return map[status?.toLowerCase()] || "pending";
}
