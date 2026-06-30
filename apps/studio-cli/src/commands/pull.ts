import chalk from "chalk";

export async function pull(options: { briefs?: boolean; prds?: boolean; tasks?: boolean }) {
  console.log(chalk.blue("⬇️ 从平台拉取数据"));

  if (options.briefs) {
    console.log(chalk.gray("拉取 Briefs..."));
  }
  if (options.prds) {
    console.log(chalk.gray("拉取 PRDs..."));
  }
  if (options.tasks) {
    console.log(chalk.gray("拉取 Tasks..."));
  }

  console.log(chalk.green("✅ 拉取完成"));
}
