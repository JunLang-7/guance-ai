import { useEffect, useState } from 'react';
import { applyProject, flushDesktop, refreshProjects } from './client';
import { Button } from '@/components/ui/Button';
import { InfoBanner } from '@/components/ui/Form';

interface CaseMeta {
  slug: string;
  name: string;
  industry: string;
  region: string;
  budgetYuan: number;
  targetLeads: number;
  leads: number;
  cpl: number;
  ctr: number;
  mape: number;
  credibility: number;
  satisfaction: number;
  fit: string;
  projectFile: string;
  reportFile: string;
}

export function CaseLibrary() {
  const [cases, setCases] = useState<CaseMeta[]>([]);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  useEffect(() => {
    const base = new URL('simulations/', window.location.href);
    void fetch(new URL('index.json', base))
      .then((response) => response.ok ? response.json() : Promise.reject(new Error(`HTTP ${response.status}`)))
      .then((items: CaseMeta[]) => setCases(items))
      .catch((error: unknown) => setMessage(`案例列表加载失败：${error instanceof Error ? error.message : '未知错误'}`));
  }, []);
  const importCase = async (item: CaseMeta) => {
    if (!window.guance) return;
    setBusy(item.slug); setMessage('');
    try {
      const base = new URL('simulations/', window.location.href);
      const response = await fetch(new URL(item.projectFile, base));
      if (!response.ok) throw new Error(`案例文件读取失败：HTTP ${response.status}`);
      const snapshot: unknown = await response.json();
      await flushDesktop();
      const project = await window.guance.invoke('projects.import', { name: `${item.name}（模拟案例）`, snapshot });
      applyProject(project);
      await refreshProjects();
      setMessage(`已导入「${item.name}」。这是演示项目，所有数据均为模拟；可在项目与备份中删除或重置。`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '导入失败');
    } finally { setBusy(''); }
  };
  return <div className="space-y-4">
    <InfoBanner tone="warning" title="模拟案例，不是企业真实数据">
      这些案例覆盖山东 5 家企业、5 个行业，用于演示“资料收集 → 研判 → A/B 方案 → 审批 → 复盘 → 历史回测”的完整过程。消费者语句、竞品观察、渠道数据和复盘结果均为模拟，不代表企业真实意见或真实经营数据。
    </InfoBanner>
    {message && <InfoBanner tone={message.startsWith('已导入') ? 'success' : 'warning'}>{message}</InfoBanner>}
    <div className="grid gap-3 md:grid-cols-2">
      {cases.map((item) => <section key={item.slug} className="rounded-xl border border-line bg-white p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div><p className="text-sm font-semibold text-ink">{item.name}</p><p className="mt-1 text-[11px] text-muted">{item.industry} · {item.region}</p></div>
          <span className="rounded-full bg-[#fdf8ee] px-2 py-0.5 text-[11px] font-semibold text-[#7b5718]">模拟</span>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] leading-5 text-muted">
          <span>预算：{item.budgetYuan.toLocaleString()} 元</span>
          <span>线索：{item.leads} / {item.targetLeads}</span>
          <span>线索成本：{item.cpl.toFixed(0)} 元</span>
          <span>CTR：{item.ctr.toFixed(2)}%</span>
          <span>MAPE：{item.mape.toFixed(1)}%</span>
          <span>可信度：{item.credibility.toFixed(1)} / 100</span>
          <span>满意度：{item.satisfaction} / 5</span>
          <span>适配性：{item.fit}</span>
        </div>
        <p className="mt-2 break-all text-[10px] text-faint">报告：案例集.md（合并版）</p>
        <Button className="mt-3" size="sm" variant="primary" disabled={busy === item.slug} onClick={() => void importCase(item)}>{busy === item.slug ? '导入中…' : '导入为演示项目'}</Button>
      </section>)}
    </div>
    <p className="text-[11px] leading-5 text-faint">导入后在工作台、市场情报、策略、复盘页查看完整数据；报告在 `simulations/reports` 目录。</p>
  </div>;
}
