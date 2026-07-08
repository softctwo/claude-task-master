import DashboardLayout from "../dashboard/layout";

export default function AgentRunsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Agent 执行</h1>
            <p className="text-slate-500 mt-1">AI Agent 执行日志和结果</p>
          </div>
          <button className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800">
            发起执行
          </button>
        </div>

        <div className="bg-white rounded-lg border border-slate-200">
          <div className="p-4 border-b border-slate-200">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="搜索执行记录..."
                className="flex-1 px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
              <select className="px-3 py-2 border border-slate-200 rounded-md text-sm">
                <option>全部状态</option>
                <option>运行中</option>
                <option>已完成</option>
                <option>失败</option>
              </select>
            </div>
          </div>
          <div className="p-8 text-center text-slate-500">
            <p>暂无执行记录</p>
            <p className="text-sm mt-1">从任务详情页发起 Agent 执行</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
