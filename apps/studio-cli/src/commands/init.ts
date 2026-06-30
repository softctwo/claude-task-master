import chalk from "chalk";
import fs from "fs-extra";
import path from "path";

export async function init(projectId: string, options: { path: string }) {
  const targetDir = path.resolve(options.path);
  const taskmasterDir = path.join(targetDir, ".taskmaster");
  const resoftDir = path.join(targetDir, ".resoft-studio");

  console.log(chalk.blue(`📁 初始化项目 ${projectId}`));
  console.log(chalk.gray(`目标目录: ${targetDir}`));

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

  console.log(chalk.green("✅ 项目初始化完成"));
  console.log(chalk.gray("  .taskmaster/      - Taskmaster 工作目录"));
  console.log(chalk.gray("  .resoft-studio/   - Resoft 扩展上下文"));
}
