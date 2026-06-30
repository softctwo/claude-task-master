import { Command } from "commander";
import chalk from "chalk";
import { login } from "./commands/login.js";
import { init } from "./commands/init.js";
import { sync } from "./commands/sync.js";
import { pull } from "./commands/pull.js";
import { push } from "./commands/push.js";
import { project } from "./commands/project.js";
import { context } from "./commands/context.js";

const program = new Command();

program
  .name("resoft-studio")
  .description("Resoft AI Delivery Studio 本地 CLI 同步工具")
  .version("0.1.0");

program
  .command("login")
  .description("登录到 Resoft AI Delivery Studio")
  .option("--server <url>", "API 服务器地址", "http://localhost:8000")
  .action(login);

program
  .command("init")
  .description("初始化项目本地工作目录")
  .argument("<project-id>", "项目 ID")
  .option("--path <dir>", "本地目录路径", ".")
  .action(init);

program
  .command("sync")
  .description("同步任务数据到/从平台")
  .option("--to-remote", "推送到远程平台")
  .option("--from-remote", "从远程平台拉取")
  .action(sync);

program
  .command("pull")
  .description("从平台拉取项目数据")
  .option("--briefs", "拉取 Briefs")
  .option("--prds", "拉取 PRDs")
  .option("--tasks", "拉取 Tasks")
  .action(pull);

program
  .command("push")
  .description("推送本地变更到平台")
  .option("--tasks", "推送任务状态变更")
  .action(push);

program
  .command("project")
  .description("项目管理")
  .option("--list", "列出项目")
  .option("--select <id>", "选择项目")
  .action(project);

program
  .command("context")
  .description("生成上下文文件供 AI 工具使用")
  .option("--output <file>", "输出文件路径", ".resoft-studio/context.md")
  .action(context);

program.parse();
