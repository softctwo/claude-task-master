import DashboardLayout from "./layout";

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">仪表盘</h1>
          <p className="text-slate-500 mt-1">概览项目交付状态</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "活跃项目", value: "0", color: "bg-blue-50 text-blue-700" },
            { label: "待办任务", value: "0", color: "bg-amber-50 text-amber-700" },
            { label: "进行中", value: "0", color: "bg-emerald-50 text-emerald-700" },
            { label: "已完成", value: "0", color: "bg-slate-50 text-slate-700" },
          ].map((stat) => (
            <div
              key={stat.label}
              className={`p-4 rounded-lg border ${stat.color} border-opacity-10`}
            >
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm mt-1 opacity-80">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">最近项目</h2>
          <p className="text-slate-500 text-sm">暂无项目，请先创建一个项目。</p>
        </div>
      </div>
    </DashboardLayout>
  );
}
