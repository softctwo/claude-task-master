import DashboardLayout from "../dashboard/layout";

export default function ProjectsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">项目</h1>
            <p className="text-slate-500 mt-1">管理所有研发项目</p>
          </div>
          <button className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800">
            创建项目
          </button>
        </div>

        <div className="bg-white rounded-lg border border-slate-200">
          <div className="p-4 border-b border-slate-200">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="搜索项目..."
                className="flex-1 px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
              <select className="px-3 py-2 border border-slate-200 rounded-md text-sm">
                <option>全部状态</option>
                <option>活跃</option>
                <option>暂停</option>
                <option>归档</option>
              </select>
            </div>
          </div>
          <div className="p-8 text-center text-slate-500">
            <p>暂无项目</p>
            <p className="text-sm mt-1">点击「创建项目」开始</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
