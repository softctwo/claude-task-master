import chalk from "chalk";
import ora from "ora";
import fs from "fs-extra";
import path from "path";
import { getApiClient, getCurrentProjectId } from "./api-client.js";

const RESOFT_DIR = ".resoft-studio";
const TASKMASTER_DIR = ".taskmaster";

export async function pull(options: { briefs?: boolean; prds?: boolean; tasks?: boolean }) {
  const projectId = await getCurrentProjectId();
  if (!projectId) {
    console.error(chalk.red("❌ 未选择项目。请先运行: resoft-studio init <project-id>"));
    process.exit(1);
  }

  console.log(chalk.blue(`⬇️ 从平台拉取数据 (项目: ${projectId})`));
  const client = await getApiClient();

  // 如果没有指定任何选项，默认拉取所有
  const pullAll = !options.briefs && !options.prds && !options.tasks;

  if (pullAll || options.briefs) {
    const spinner = ora("拉取 Briefs...").start();
    try {
      const { data } = await client.get("/briefs", {
        params: { project_id: projectId, page_size: 100 },
      });
      const briefs = data.items || [];
      const briefsDir = path.join(RESOFT_DIR, "briefs");
      await fs.ensureDir(briefsDir);

      for (const brief of briefs) {
        const briefFile = path.join(briefsDir, `${brief.brief_id}.md`);
        let content = `# ${brief.title}\n\n`;
        content += `**状态:** ${brief.status} | **版本:** ${brief.version}\n\n`;
        if (brief.background) content += `## 背景\n\n${brief.background}\n\n`;
        if (brief.problem_statement) content += `## 问题陈述\n\n${brief.problem_statement}\n\n`;
        if (brief.target_users) content += `## 目标用户\n\n${brief.target_users}\n\n`;
        if (brief.goals?.length) {
          content += `## 目标\n\n${brief.goals.map((g: string) => `- ${g}`).join("\n")}\n\n`;
        }
        if (brief.non_goals?.length) {
          content += `## 非目标\n\n${brief.non_goals.map((g: string) => `- ${g}`).join("\n")}\n\n`;
        }
        if (brief.scope) content += `## 范围\n\n${brief.scope}\n\n`;
        if (brief.user_stories?.length) {
          content += `## 用户故事\n\n${brief.user_stories.map((us: string) => `- ${us}`).join("\n")}\n\n`;
        }
        if (brief.acceptance_criteria?.length) {
          content += `## 验收标准\n\n${brief.acceptance_criteria.map((c: string) => `- ${c}`).join("\n")}\n\n`;
        }
        if (brief.constraints) content += `## 约束条件\n\n${brief.constraints}\n\n`;
        await fs.writeFile(briefFile, content);
      }

      spinner.succeed(`已拉取 ${briefs.length} 个 Briefs`);
    } catch (error: any) {
      spinner.fail(`拉取 Briefs 失败: ${error.message || String(error)}`);
    }
  }

  if (pullAll || options.prds) {
    const spinner = ora("拉取 PRDs...").start();
    try {
      const { data } = await client.get("/prds", {
        params: { project_id: projectId, page_size: 100 },
      });
      const prds = data.items || [];
      const prdsDir = path.join(RESOFT_DIR, "prds");
      await fs.ensureDir(prdsDir);

      for (const prd of prds) {
        const prdFile = path.join(prdsDir, `${prd.prd_id}.md`);
        const content = prd.content_markdown || `# PRD: ${prd.prd_id}\n\n_Generated from brief ${prd.brief_id}_\n\n`;
        await fs.writeFile(prdFile, content);
      }

      spinner.succeed(`已拉取 ${prds.length} 个 PRDs`);
    } catch (error: any) {
      spinner.fail(`拉取 PRDs 失败: ${error.message || String(error)}`);
    }
  }

  if (pullAll || options.tasks) {
    const spinner = ora("拉取 Tasks...").start();
    try {
      const { data } = await client.get("/tasks", {
        params: { project_id: projectId, page_size: 100 },
      });
      const tasks = data.items || [];
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
          parent_task_id: task.parent_task_id,
          assignee_id: task.assignee_id,
          _resoft_meta: {
            task_id: task.task_id,
            project_id: task.project_id,
            updated_at: task.updated_at,
          },
        }, { spaces: 2 });
      }

      spinner.succeed(`已拉取 ${tasks.length} 个 Tasks`);
    } catch (error: any) {
      spinner.fail(`拉取 Tasks 失败: ${error.message || String(error)}`);
    }
  }

  console.log(chalk.green("✅ 拉取完成"));
}
