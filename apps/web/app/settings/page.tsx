import DashboardLayout from "../dashboard/layout";

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">设置</h1>
          <p className="text-slate-500 mt-1">系统配置和模型管理</p>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 divide-y divide-slate-200">
          <div className="p-6">
            <h3 className="font-semibold text-slate-900 mb-2">模型配置</h3>
            <p className="text-sm text-slate-500 mb-4">配置 AI 模型供应商和 API Key</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">供应商</label>
                <select className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm">
                  <option>OpenAI</option>
                  <option>Anthropic</option>
                  <option>DeepSeek</option>
                  <option>智谱</option>
                  <option>本地模型</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">模型</label>
                <input
                  type="text"
                  defaultValue="gpt-4"
                  className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">API Key</label>
                <input
                  type="password"
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm"
                />
              </div>
            </div>
          </div>

          <div className="p-6">
            <h3 className="font-semibold text-slate-900 mb-2">安全策略</h3>
            <p className="text-sm text-slate-500 mb-4">配置数据安全和模型调用策略</p>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" />
                <span className="text-sm text-slate-700">允许调用外部模型</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-sm text-slate-700">敏感信息脱敏</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-sm text-slate-700">记录所有操作审计日志</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
