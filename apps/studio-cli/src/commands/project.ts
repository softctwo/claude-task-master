import chalk from "chalk";
import ora from "ora";
import { getApiClient, setCurrentProjectId, getCurrentProjectId } from "./api-client.js";

export async function project(options: { list?: boolean; select?: string }) {
  const client = await getApiClient();

  if (options.list) {
    const spinner = ora("获取项目列表...").start();
    try {
      const { data } = await client.get("/projects", {
        params: { page_size: 100 },
      });
      const projects = data.items || [];
      spinner.stop();

      if (projects.length === 0) {
        console.log(chalk.yellow("⚠️ 暂无项目"));
        return;
      }

      const currentProjectId = await getCurrentProjectId();

      console.log(chalk.blue("📋 项目列表"));
      console.log(chalk.gray("─".repeat(60)));
      for (const project of projects) {
        const isCurrent = project.project_id === currentProjectId;
        const marker = isCurrent ? chalk.green("● ") : "  ";
        console.log(`${marker}${chalk.bold(project.name)} ${chalk.gray(`(${project.project_id})`)}`);
        console.log(`     状态: ${project.status} | 描述: ${project.description || "无"}`);
      }
      console.log(chalk.gray("─".repeat(60)));
      console.log(chalk.gray(`共 ${projects.length} 个项目`));
      if (currentProjectId) {
        console.log(chalk.gray(`当前项目: ${currentProjectId}`));
      }
    } catch (error: any) {
      spinner.fail(`获取项目列表失败: ${error.message || String(error)}`);
    }
  }

  if (options.select) {
    const spinner = ora(`验证项目 ${options.select}...`).start();
    try {
      const { data: project } = await client.get(`/projects/${options.select}`);
      await setCurrentProjectId(options.select);
      spinner.succeed(`已选择项目: ${project.name} (${options.select})`);
    } catch (error: any) {
      spinner.fail(`选择项目失败: ${error.message || String(error)}`);
      process.exit(1);
    }
  }

  // 如果没有指定任何选项，显示当前项目
  if (!options.list && !options.select) {
    const currentProjectId = await getCurrentProjectId();
    if (currentProjectId) {
      try {
        const { data: project } = await client.get(`/projects/${currentProjectId}`);
        console.log(chalk.blue("📌 当前项目"));
        console.log(`  名称: ${project.name}`);
        console.log(`  ID: ${project.project_id}`);
        console.log(`  状态: ${project.status}`);
        console.log(`  描述: ${project.description || "无"}`);
      } catch (error: any) {
        console.log(chalk.yellow("⚠️ 当前项目信息无法获取"));
        console.log(chalk.gray(`  项目ID: ${currentProjectId}`));
      }
    } else {
      console.log(chalk.yellow("⚠️ 未选择项目"));
      console.log(chalk.gray("  使用: resoft-studio project --select <project-id>"));
      console.log(chalk.gray("  或:  resoft-studio project --list"));
    }
  }
}
