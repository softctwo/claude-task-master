import DashboardLayout from "../dashboard/layout";

export default function TasksPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">任务</h1>
            <p className="text-slate-500 mt-1">任务树、看板和依赖管理</p>
          </div>
          <button className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800">
            生成任务
          </button>
        </div>

        <div className="flex gap-2 border-b border-slate-200 pb-2">
          {["看板", "列表", "树形", "依赖图"].map((view) => (
            <button
              key={view}
              className={`px-3 py-1.5 text-sm rounded-md ${
                view === "看板"
                  ? "bg-slate-100 text-slate-900 font-medium"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {view}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {["待办", "进行中", "已完成", "阻塞"].map((status) => (
            <div key={status} className="bg-white rounded-lg border border-slate-200 p-4 min-h-[200px]">
              <h3 className="font-semibold text-slate-900 mb-3">{status}</h3>
              <p className="text-sm text-slate-500">暂无任务</p>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
