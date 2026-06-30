import chalk from "chalk";

export async function project(options: { list?: boolean; select?: string }) {
  if (options.list) {
    console.log(chalk.blue("📋 项目列表"));
    // TODO: 调用 API 列出项目
    console.log(chalk.gray("  (暂无项目)"));
  }

  if (options.select) {
    console.log(chalk.blue(`📌 选择项目: ${options.select}`));
    // TODO: 保存当前项目到本地配置
  }
}
