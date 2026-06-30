import DashboardLayout from "../dashboard/layout";

export default function KnowledgePage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">知识库</h1>
            <p className="text-slate-500 mt-1">项目文档和知识沉淀</p>
          </div>
          <button className="px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800">
            上传文档
          </button>
        </div>

        <div className="bg-white rounded-lg border border-slate-200">
          <div className="p-4 border-b border-slate-200">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="搜索知识文档..."
                className="flex-1 px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
              <select className="px-3 py-2 border border-slate-200 rounded-md text-sm">
                <option>全部类型</option>
                <option>文档</option>
                <option>会议纪要</option>
                <option>代码说明</option>
                <option>SOP</option>
              </select>
            </div>
          </div>
          <div className="p-8 text-center text-slate-500">
            <p>暂无知识文档</p>
            <p className="text-sm mt-1">上传文档开始使用知识库</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
