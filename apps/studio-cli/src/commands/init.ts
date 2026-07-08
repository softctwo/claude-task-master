import chalk from "chalk";
import inquirer from "inquirer";
import fs from "fs-extra";
import path from "path";
import { getApiClient, getCurrentProjectId, setCurrentProjectId } from "./api-client.js";

export async function init(projectId: string, options: { path: string }) {
  const targetDir = path.resolve(options.path);
  const taskmasterDir = path.join(targetDir, ".taskmaster");
  const resoftDir = path.join(targetDir, ".resoft-studio");

  console.log(chalk.blue(`📁 初始化项目 ${projectId}`));
  console.log(chalk.gray(`目标目录: ${targetDir}`));

  const client = await getApiClient();

  // 验证项目存在
  try {
    const { data: project } = await client.get(`/projects/${projectId}`);
    console.log(chalk.green(`  项目确认: ${project.name}`));
  } catch (error: any) {
    console.error(chalk.red("❌ 无法获取项目信息"));
    console.error(chalk.red(error.message || String(error)));
    process.exit(1);
  }

  // 创建 .taskmaster/ 目录（保持与 Taskmaster 兼容）
  await fs.ensureDir(taskmasterDir);
  await fs.ensureDir(path.join(taskmasterDir, "tasks"));
  await fs.ensureDir(path.join(taskmasterDir, "docs"));
  await fs.ensureDir(path.join(taskmasterDir, "reports"));
  await fs.writeJson(path.join(taskmasterDir, "config.json"), {
    projectId,
    version: "1.0.0",
  });

  // 创建 .resoft-studio/ 目录（Resoft 扩展上下文）
  await fs.ensureDir(resoftDir);
  await fs.ensureDir(path.join(resoftDir, "briefs"));
  await fs.ensureDir(path.join(resoftDir, "prds"));
  await fs.ensureDir(path.join(resoftDir, "context"));
  await fs.ensureDir(path.join(resoftDir, "agent-instructions"));
  await fs.writeJson(path.join(resoftDir, "project.json"), {
    projectId,
    syncState: {},
  });
  await fs.writeJson(path.join(resoftDir, "sync-state.json"), {
    lastSyncAt: null,
    syncedTasks: [],
  });

  // 设置为当前项目
  await setCurrentProjectId(projectId);

  console.log(chalk.green("✅ 项目初始化完成"));
  console.log(chalk.gray("  .taskmaster/      - Taskmaster 工作目录"));
  console.log(chalk.gray("  .resoft-studio/   - Resoft 扩展上下文"));
}
