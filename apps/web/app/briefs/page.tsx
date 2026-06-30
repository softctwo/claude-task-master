import DashboardLayout from "../dashboard/layout";

export default function BriefsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Briefs</h1>
            <p className="text-slate-500 mt-1">需求澄清和产品意图</p>
          </div>
          <button className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800">
            创建 Brief
          </button>
        </div>

        <div className="grid gap-4">
          {[
            { status: "draft", label: "草稿" },
            { status: "reviewing", label: "评审中" },
            { status: "approved", label: "已审批" },
          ].map((col) => (
            <div key={col.status} className="bg-white rounded-lg border border-slate-200 p-4">
              <h3 className="font-semibold text-slate-900 mb-3">{col.label}</h3>
              <p className="text-sm text-slate-500">暂无 Brief</p>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
