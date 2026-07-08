import axios, { AxiosInstance, AxiosError } from "axios";
import fs from "fs-extra";
import path from "path";
import os from "os";

const CONFIG_DIR = path.join(os.homedir(), ".resoft-studio");
const CONFIG_FILE = path.join(CONFIG_DIR, "config.json");

export interface StudioConfig {
  server: string;
  email?: string;
  token?: string;
  currentProjectId?: string;
}

export async function loadConfig(): Promise<StudioConfig> {
  if (await fs.pathExists(CONFIG_FILE)) {
    return await fs.readJson(CONFIG_FILE);
  }
  return { server: "http://localhost:8000" };
}

export async function saveConfig(config: StudioConfig): Promise<void> {
  await fs.ensureDir(CONFIG_DIR);
  await fs.writeJson(CONFIG_FILE, config, { spaces: 2 });
}

export function createApiClient(config: StudioConfig): AxiosInstance {
  const client = axios.create({
    baseURL: `${config.server}/api/v1`,
    timeout: 30000,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Request interceptor: inject auth token
  client.interceptors.request.use(
    (request: any) => {
      if (config.token) {
        request.headers.Authorization = `Bearer ${config.token}`;
      }
      return request;
    },
    (error: any) => Promise.reject(error)
  );

  // Response interceptor: handle common errors
  client.interceptors.response.use(
    (response: any) => response,
    (error: AxiosError) => {
      if (error.response) {
        const status = error.response.status;
        const data = error.response.data as any;
        const message = data?.detail || data?.message || error.message;

        if (status === 401) {
          return Promise.reject(new Error(`认证失败: ${message}。请运行 "resoft-studio login" 重新登录。`));
        }
        if (status === 403) {
          return Promise.reject(new Error(`权限不足: ${message}`));
        }
        if (status === 404) {
          return Promise.reject(new Error(`资源未找到: ${message}`));
        }
        if (status === 409) {
          return Promise.reject(new Error(`资源冲突: ${message}`));
        }
        if (status >= 500) {
          return Promise.reject(new Error(`服务器错误 (${status}): ${message}`));
        }
        return Promise.reject(new Error(`请求失败 (${status}): ${message}`));
      }
      if (error.code === "ECONNREFUSED") {
        return Promise.reject(new Error(`无法连接到服务器 ${config.server}。请确认后端服务已启动。`));
      }
      if (error.code === "ETIMEDOUT" || error.code === "ECONNABORTED") {
        return Promise.reject(new Error(`请求超时。服务器 ${config.server} 响应过慢。`));
      }
      return Promise.reject(error);
    }
  );

  return client;
}

export async function getApiClient(): Promise<AxiosInstance> {
  const config = await loadConfig();
  if (!config.token) {
    throw new Error('未登录。请运行 "resoft-studio login" 进行登录。');
  }
  return createApiClient(config);
}

export async function getServerUrl(): Promise<string> {
  const config = await loadConfig();
  return config.server;
}

export async function getCurrentProjectId(): Promise<string | undefined> {
  const config = await loadConfig();
  return config.currentProjectId;
}

export async function setCurrentProjectId(projectId: string): Promise<void> {
  const config = await loadConfig();
  config.currentProjectId = projectId;
  await saveConfig(config);
}
