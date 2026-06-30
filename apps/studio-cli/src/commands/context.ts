import chalk from "chalk";
import fs from "fs-extra";
import path from "path";

export async function context(options: { output: string }) {
  console.log(chalk.blue("📝 生成上下文文件"));

  const resoftDir = ".resoft-studio";
  const taskmasterDir = ".taskmaster";

  // 收集项目上下文
  let contextContent = "# Resoft AI Delivery Studio - 项目上下文\n\n";

  // 读取 Briefs
  const briefsDir = path.join(resoftDir, "briefs");
  if (await fs.pathExists(briefsDir)) {
    const briefs = await fs.readdir(briefsDir);
    contextContent += "## Briefs\n\n";
    for (const brief of briefs) {
      const content = await fs.readFile(path.join(briefsDir, brief), "utf-8");
      contextContent += `### ${brief}\n\n${content}\n\n`;
    }
  }

  // 读取 PRDs
  const prdsDir = path.join(resoftDir, "prds");
  if (await fs.pathExists(prdsDir)) {
    const prds = await fs.readdir(prdsDir);
    contextContent += "## PRDs\n\n";
    for (const prd of prds) {
      const content = await fs.readFile(path.join(prdsDir, prd), "utf-8");
      contextContent += `### ${prd}\n\n${content}\n\n`;
    }
  }

  // 读取 Tasks
  const tasksDir = path.join(taskmasterDir, "tasks");
  if (await fs.pathExists(tasksDir)) {
    const tasks = await fs.readdir(tasksDir);
    contextContent += "## Tasks\n\n";
    for (const task of tasks) {
      const content = await fs.readFile(path.join(tasksDir, task), "utf-8");
      contextContent += `### ${task}\n\n${content}\n\n`;
    }
  }

  await fs.writeFile(options.output, contextContent);
  console.log(chalk.green(`✅ 上下文文件已生成: ${options.output}`));
}
