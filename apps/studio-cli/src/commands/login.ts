import chalk from "chalk";
import inquirer from "inquirer";
import { loadConfig, saveConfig, createApiClient } from "./api-client.js";

export async function login(options: { server: string }) {
  console.log(chalk.blue("🔐 登录到 Resoft AI Delivery Studio"));

  const answers = await inquirer.prompt([
    { type: "input", name: "email", message: "邮箱:" },
    { type: "password", name: "password", message: "密码:", mask: "*" },
  ]);

  const client = createApiClient({ server: options.server });

  try {
    const { data } = await client.post("/auth/login", {
      email: answers.email,
      password: answers.password,
    });

    const token = data.access_token;
    const user = data.user;

    await saveConfig({
      server: options.server,
      email: answers.email,
      token,
    });

    console.log(chalk.green("✅ 登录成功"));
    console.log(chalk.gray(`  用户: ${user.name} (${user.email})`));
    console.log(chalk.gray(`  角色: ${user.role}`));
    console.log(chalk.gray(`  服务器: ${options.server}`));
  } catch (error: any) {
    console.error(chalk.red("❌ 登录失败"));
    console.error(chalk.red(error.message || String(error)));
    process.exit(1);
  }
}
