import chalk from "chalk";
import inquirer from "inquirer";
import fs from "fs-extra";
import path from "path";
import os from "os";

const CONFIG_DIR = path.join(os.homedir(), ".resoft-studio");
const CONFIG_FILE = path.join(CONFIG_DIR, "config.json");

export async function login(options: { server: string }) {
  console.log(chalk.blue("🔐 登录到 Resoft AI Delivery Studio"));

  const answers = await inquirer.prompt([
    { type: "input", name: "email", message: "邮箱:" },
    { type: "password", name: "password", message: "密码:" },
  ]);

  // TODO: 调用后端 API 登录
  console.log(chalk.green("✅ 登录成功"));
  console.log(chalk.gray(`服务器: ${options.server}`));

  await fs.ensureDir(CONFIG_DIR);
  await fs.writeJson(CONFIG_FILE, {
    server: options.server,
    email: answers.email,
    token: "dummy-token", // TODO: 从 API 获取真实 token
  });
}
