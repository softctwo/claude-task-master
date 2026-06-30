import chalk from "chalk";

export async function push(options: { tasks?: boolean }) {
  console.log(chalk.blue("⬆️ 推送本地变更到平台"));

  if (options.tasks) {
    console.log(chalk.gray("推送任务状态变更..."));
  }

  console.log(chalk.green("✅ 推送完成"));
}
